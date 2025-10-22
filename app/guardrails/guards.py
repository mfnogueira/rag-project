"""
Configuração de Guards para o projeto de súmulas TCEMG.

Fase 1: Validators básicos (toxicidade, tamanho)
Fase 2: Validators avançados (alucinações, súmulas citadas, tom jurídico)
"""

from guardrails import Guard
from guardrails.validator_base import (
    Validator,
    register_validator,
    ValidationResult,
)
from typing import Dict, Any, List, Optional
import re


@register_validator(name="basic_toxic_language", data_type="string")
class BasicToxicLanguage(Validator):
    """
    Validator simples para detectar linguagem tóxica/ofensiva.

    Versão básica que não requer tokens do Guardrails Hub.
    """

    # Lista de termos ofensivos (expandir conforme necessário)
    TOXIC_TERMS = [
        "idiota", "burro", "estúpido", "imbecil", "otário",
        "merda", "porra", "caralho", "buceta", "cu",
        "fdp", "pqp", "vsf", "vai tomar no cu"
    ]

    def __init__(self, threshold: float = 0.5, on_fail: str = "fix", **kwargs):
        super().__init__(on_fail=on_fail, **kwargs)
        self.threshold = threshold

    def validate(self, value: str, metadata: Dict[str, Any]) -> ValidationResult:
        """Valida se o texto contém linguagem tóxica."""

        if not value:
            return ValidationResult(
                outcome="pass",
                metadata={"checked": False, "reason": "empty_input"}
            )

        value_lower = value.lower()
        found_toxic = []

        for term in self.TOXIC_TERMS:
            if term in value_lower:
                found_toxic.append(term)

        if found_toxic:
            # Remove termos tóxicos
            clean_value = value
            for term in found_toxic:
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                clean_value = pattern.sub("[removido]", clean_value)

            return ValidationResult(
                outcome="fail",
                error_spans=None,
                fixed_value=clean_value,
                error_message=f"Linguagem tóxica detectada: {', '.join(found_toxic)}",
                metadata={"toxic_terms_found": found_toxic}
            )

        return ValidationResult(
            outcome="pass",
            metadata={"toxic_terms_found": []}
        )


@register_validator(name="profanity_check", data_type="string")
class ProfanityCheck(Validator):
    """
    Validator para detectar palavrões e linguagem imprópria.
    """

    PROFANITY_WORDS = [
        "porra", "caralho", "merda", "puta", "buceta",
        "cu", "foder", "foda", "fdp", "pqp", "vsf"
    ]

    def __init__(self, on_fail: str = "exception", **kwargs):
        super().__init__(on_fail=on_fail, **kwargs)

    def validate(self, value: str, metadata: Dict[str, Any]) -> ValidationResult:
        """Valida se o texto contém palavrões."""

        if not value:
            return ValidationResult(outcome="pass")

        value_lower = value.lower()
        found_profanity = []

        for word in self.PROFANITY_WORDS:
            if word in value_lower:
                found_profanity.append(word)

        if found_profanity:
            return ValidationResult(
                outcome="fail",
                error_spans=None,
                error_message=f"Palavrões detectados: {', '.join(found_profanity)}",
                metadata={"profanity_found": found_profanity}
            )

        return ValidationResult(
            outcome="pass",
            metadata={"profanity_found": []}
        )


@register_validator(name="response_length", data_type="string")
class ResponseLength(Validator):
    """
    Validator para garantir que a resposta tenha tamanho adequado.
    """

    def __init__(
        self,
        min_length: int = 50,
        max_length: int = 2000,
        on_fail: str = "reask",
        **kwargs
    ):
        super().__init__(on_fail=on_fail, **kwargs)
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, value: str, metadata: Dict[str, Any]) -> ValidationResult:
        """Valida o tamanho da resposta."""

        if not value:
            return ValidationResult(
                outcome="fail",
                error_message="Resposta vazia"
            )

        length = len(value)

        if length < self.min_length:
            return ValidationResult(
                outcome="fail",
                error_spans=None,
                error_message=f"Resposta muito curta ({length} chars). Mínimo: {self.min_length}",
                metadata={"length": length, "min": self.min_length, "max": self.max_length}
            )

        if length > self.max_length:
            return ValidationResult(
                outcome="fail",
                error_spans=None,
                fixed_value=value[:self.max_length] + "...",
                error_message=f"Resposta muito longa ({length} chars). Máximo: {self.max_length}",
                metadata={"length": length, "min": self.min_length, "max": self.max_length}
            )

        return ValidationResult(
            outcome="pass",
            metadata={"length": length, "min": self.min_length, "max": self.max_length}
        )


# ========================================
# FASE 2: VALIDATORS AVANÇADOS
# ========================================

@register_validator(name="hallucination_detection", data_type="string")
class HallucinationDetection(Validator):
    """
    Validator para detectar alucinações (informações inventadas pelo LLM).

    Técnicas utilizadas:
    1. Verifica se súmulas citadas existem no contexto recuperado
    2. Detecta afirmações categóricas sem base no contexto
    3. Identifica informações específicas não presentes nos documentos

    Parâmetros:
        threshold (float): Limite de tolerância (0.0 a 1.0). Quanto menor, mais rigoroso.
        on_fail (str): Ação ao falhar ("exception", "reask", "fix")
    """

    # Padrões que indicam afirmações categóricas
    ASSERTIVE_PATTERNS = [
        r"a súmula \d+ estabelece que",
        r"conforme a súmula \d+",
        r"segundo a súmula \d+",
        r"a súmula determina",
        r"está previsto na súmula",
    ]

    # Palavras que indicam incerteza (BOAS - reduzem chance de alucinação)
    UNCERTAINTY_MARKERS = [
        "possivelmente", "provavelmente", "aparentemente",
        "pode ser", "talvez", "segundo os documentos",
        "conforme encontrado", "baseado no contexto"
    ]

    def __init__(
        self,
        threshold: float = 0.7,
        on_fail: str = "reask",
        **kwargs
    ):
        super().__init__(on_fail=on_fail, **kwargs)
        self.threshold = threshold

    def validate(self, value: str, metadata: Dict[str, Any]) -> ValidationResult:
        """
        Valida se a resposta contém alucinações.

        Metadata esperado:
            - context_docs: Lista de documentos recuperados
            - retrieved_sumulas: Lista de números de súmulas recuperadas
        """

        if not value:
            return ValidationResult(
                outcome="pass",
                metadata={"checked": False, "reason": "empty_response"}
            )

        # Extrai números de súmulas mencionadas na resposta
        cited_sumulas = self._extract_sumula_numbers(value)

        # Obtém súmulas que realmente foram recuperadas
        retrieved_sumulas = metadata.get("retrieved_sumulas", [])
        context_text = metadata.get("context_text", "")

        issues = []
        hallucination_score = 0.0

        # 1. Verifica súmulas citadas vs recuperadas
        if cited_sumulas:
            fabricated_sumulas = [
                s for s in cited_sumulas
                if s not in retrieved_sumulas
            ]

            if fabricated_sumulas:
                issues.append(
                    f"Súmulas citadas mas não recuperadas: {', '.join(fabricated_sumulas)}"
                )
                hallucination_score += 0.5

        # 2. Verifica afirmações categóricas
        assertive_count = 0
        for pattern in self.ASSERTIVE_PATTERNS:
            matches = re.findall(pattern, value.lower())
            assertive_count += len(matches)

        # 3. Verifica marcadores de incerteza (BONS)
        uncertainty_count = sum(
            1 for marker in self.UNCERTAINTY_MARKERS
            if marker in value.lower()
        )

        # 4. Calcula score de confiança baseado em contexto
        if context_text:
            # Verifica se trechos da resposta aparecem no contexto
            response_sentences = [
                s.strip() for s in value.split('.')
                if len(s.strip()) > 20
            ]

            grounded_sentences = 0
            for sentence in response_sentences[:5]:  # Verifica primeiras 5 frases
                # Remove números de súmulas para comparação mais genérica
                clean_sentence = re.sub(r'súmula \d+', 'súmula', sentence.lower())
                clean_context = re.sub(r'súmula \d+', 'súmula', context_text.lower())

                # Verifica se palavras-chave da frase estão no contexto
                words = [w for w in clean_sentence.split() if len(w) > 4]
                if words:
                    words_in_context = sum(
                        1 for w in words if w in clean_context
                    )
                    if words_in_context / len(words) > 0.5:
                        grounded_sentences += 1

            if response_sentences:
                grounding_ratio = grounded_sentences / len(response_sentences[:5])
                if grounding_ratio < 0.3:
                    issues.append("Resposta parece não ter base no contexto recuperado")
                    hallucination_score += 0.3

        # 5. Ajusta score baseado em incerteza
        if assertive_count > 3 and uncertainty_count == 0:
            issues.append("Muitas afirmações categóricas sem marcadores de incerteza")
            hallucination_score += 0.2

        # Decisão final
        validation_metadata = {
            "cited_sumulas": cited_sumulas,
            "retrieved_sumulas": retrieved_sumulas,
            "hallucination_score": round(hallucination_score, 2),
            "assertive_count": assertive_count,
            "uncertainty_count": uncertainty_count,
            "issues": issues
        }

        if hallucination_score >= self.threshold:
            return ValidationResult(
                outcome="fail",
                error_spans=None,
                error_message=f"Possível alucinação detectada (score: {hallucination_score:.2f}). {'; '.join(issues)}",
                metadata=validation_metadata
            )

        return ValidationResult(
            outcome="pass",
            metadata=validation_metadata
        )

    def _extract_sumula_numbers(self, text: str) -> List[str]:
        """Extrai números de súmulas mencionadas no texto."""
        # Padrões: "Súmula 70", "súmula nº 112", "Súmula N° 85"
        patterns = [
            r'súmula\s+n?º?\s*(\d+)',
            r'sumula\s+n?º?\s*(\d+)',
        ]

        numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            numbers.extend(matches)

        return list(set(numbers))  # Remove duplicatas


@register_validator(name="valid_sumula_reference", data_type="string")
class ValidSumulaReference(Validator):
    """
    Validator para garantir que súmulas citadas são válidas e estão formatadas corretamente.

    Verifica:
    1. Números de súmulas válidos (1-200 para TCEMG)
    2. Formato correto de citação
    3. Súmulas existem no banco de dados recuperado

    Parâmetros:
        min_sumula (int): Número mínimo válido de súmula (padrão: 1)
        max_sumula (int): Número máximo válido de súmula (padrão: 200)
        on_fail (str): Ação ao falhar ("exception", "reask", "fix")
    """

    def __init__(
        self,
        min_sumula: int = 1,
        max_sumula: int = 200,
        on_fail: str = "reask",
        **kwargs
    ):
        super().__init__(on_fail=on_fail, **kwargs)
        self.min_sumula = min_sumula
        self.max_sumula = max_sumula

    def validate(self, value: str, metadata: Dict[str, Any]) -> ValidationResult:
        """
        Valida se as súmulas citadas são válidas.

        Metadata esperado:
            - retrieved_sumulas: Lista de números de súmulas recuperadas
            - all_valid_sumulas: Lista de todas as súmulas válidas no sistema (opcional)
        """

        if not value:
            return ValidationResult(
                outcome="pass",
                metadata={"checked": False, "reason": "empty_response"}
            )

        # Extrai números de súmulas citadas
        cited_sumulas = self._extract_sumula_numbers(value)

        if not cited_sumulas:
            # Sem súmulas citadas, não há o que validar
            return ValidationResult(
                outcome="pass",
                metadata={"cited_sumulas": [], "validation": "no_sumulas_cited"}
            )

        retrieved_sumulas = metadata.get("retrieved_sumulas", [])
        all_valid_sumulas = metadata.get("all_valid_sumulas", [])

        issues = []
        invalid_sumulas = []
        out_of_range_sumulas = []
        not_retrieved_sumulas = []

        for num_str in cited_sumulas:
            try:
                num = int(num_str)

                # Verifica se está no range válido
                if num < self.min_sumula or num > self.max_sumula:
                    out_of_range_sumulas.append(num_str)
                    issues.append(
                        f"Súmula {num_str} fora do range válido ({self.min_sumula}-{self.max_sumula})"
                    )

                # Verifica se foi recuperada
                elif retrieved_sumulas and num_str not in retrieved_sumulas:
                    not_retrieved_sumulas.append(num_str)
                    issues.append(
                        f"Súmula {num_str} citada mas não foi recuperada"
                    )

                # Verifica se existe no sistema (se fornecido)
                elif all_valid_sumulas and num_str not in all_valid_sumulas:
                    invalid_sumulas.append(num_str)
                    issues.append(
                        f"Súmula {num_str} não existe no sistema"
                    )

            except ValueError:
                invalid_sumulas.append(num_str)
                issues.append(f"Número de súmula inválido: {num_str}")

        # Verifica formato de citação
        citation_issues = self._check_citation_format(value, cited_sumulas)
        issues.extend(citation_issues)

        # Metadados de validação
        validation_metadata = {
            "cited_sumulas": cited_sumulas,
            "retrieved_sumulas": retrieved_sumulas,
            "invalid_sumulas": invalid_sumulas,
            "out_of_range_sumulas": out_of_range_sumulas,
            "not_retrieved_sumulas": not_retrieved_sumulas,
            "citation_format_issues": citation_issues,
            "total_issues": len(issues)
        }

        # Decide se passou ou falhou
        has_critical_issues = bool(
            invalid_sumulas or out_of_range_sumulas
        )

        if has_critical_issues:
            return ValidationResult(
                outcome="fail",
                error_spans=None,
                error_message=f"Súmulas inválidas detectadas. {'; '.join(issues[:3])}",
                metadata=validation_metadata
            )

        # Aviso se citou súmulas não recuperadas (menos crítico)
        if not_retrieved_sumulas:
            validation_metadata["warning"] = f"Súmulas citadas não recuperadas: {', '.join(not_retrieved_sumulas)}"

        return ValidationResult(
            outcome="pass",
            metadata=validation_metadata
        )

    def _extract_sumula_numbers(self, text: str) -> List[str]:
        """Extrai números de súmulas mencionadas no texto."""
        patterns = [
            r'súmula\s+n?º?\s*(\d+)',
            r'sumula\s+n?º?\s*(\d+)',
            r'súm\.\s*(\d+)',
        ]

        numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            numbers.extend(matches)

        return list(set(numbers))  # Remove duplicatas

    def _check_citation_format(self, text: str, cited_sumulas: List[str]) -> List[str]:
        """
        Verifica se as citações estão formatadas corretamente.

        Formato correto: "Súmula nº XX" ou "Súmula XX"
        Formato incorreto: "sumula XX", "Súmula numero XX"
        """
        issues = []

        # Verifica padrões incorretos comuns
        incorrect_patterns = [
            (r'sumula\s+\d+', "Usar 'Súmula' com acento"),
            (r'súmula\s+numero\s+\d+', "Usar 'Súmula nº' ao invés de 'Súmula numero'"),
            (r'súmula\s+n\.\s+\d+', "Usar 'Súmula nº' ao invés de 'Súmula n.'"),
        ]

        for pattern, suggestion in incorrect_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append(f"Formato incorreto detectado. Sugestão: {suggestion}")

        return issues


def create_basic_guard() -> Guard:
    """
    Cria um Guard básico para o projeto de súmulas TCEMG.

    Fase 1: Guard simples com validators básicos.

    Returns:
        Guard configurado com validators básicos

    Example:
        >>> from app.guardrails import create_basic_guard
        >>> guard = create_basic_guard()
        >>> result = guard.validate("Texto com merda aqui")
        >>> print(result.validated_output)  # "Texto com [removido] aqui"
    """

    guard = Guard(
        name="sumulas_basic_guard",
        description="Guard básico para validação de inputs e outputs"
    )

    # Input Guards (validação da pergunta do usuário)
    guard.use(
        ProfanityCheck(on_fail="exception"),
        on="prompt"  # Valida o input
    )

    # Output Guards (validação da resposta do LLM)
    guard.use_many(
        BasicToxicLanguage(threshold=0.5, on_fail="fix"),
        ResponseLength(min_length=100, max_length=2000, on_fail="reask"),
        on="output"  # Valida o output
    )

    return guard


def validate_input(text: str) -> Dict[str, Any]:
    """
    Valida o input do usuário antes de processar.

    Args:
        text: Texto da pergunta do usuário

    Returns:
        Dict com 'is_valid', 'cleaned_text' e 'errors'

    Example:
        >>> result = validate_input("Me explica a súmula 70, porra!")
        >>> print(result['is_valid'])  # False
        >>> print(result['errors'])  # ['Palavrões detectados: porra']
    """

    validator = ProfanityCheck(on_fail="exception")

    try:
        result = validator.validate(text, {})

        if result.outcome == "pass":
            return {
                "is_valid": True,
                "cleaned_text": text,
                "errors": []
            }
        else:
            return {
                "is_valid": False,
                "cleaned_text": text,
                "errors": [result.error_message] if result.error_message else []
            }

    except Exception as e:
        return {
            "is_valid": False,
            "cleaned_text": text,
            "errors": [str(e)]
        }


def validate_output(
    text: str,
    context_docs: Optional[List[Any]] = None,
    enable_hallucination_detection: bool = True
) -> Dict[str, Any]:
    """
    Valida o output do LLM antes de retornar ao usuário.

    Args:
        text: Resposta gerada pelo LLM
        context_docs: Lista de documentos recuperados (para detecção de alucinações)
        enable_hallucination_detection: Se True, ativa detecção de alucinações

    Returns:
        Dict com 'is_valid', 'cleaned_text' e 'validation_info'

    Example:
        >>> result = validate_output("Resposta com merda aqui")
        >>> print(result['cleaned_text'])  # "Resposta com [removido] aqui"
    """

    validators = [
        BasicToxicLanguage(threshold=0.5, on_fail="fix"),
        ResponseLength(min_length=100, max_length=2000, on_fail="fix")
    ]

    # Prepara metadata para detecção de alucinações
    hallucination_metadata = {}
    if enable_hallucination_detection and context_docs:
        # Extrai números de súmulas dos documentos recuperados
        retrieved_sumulas = []
        context_text_parts = []

        for doc in context_docs:
            if hasattr(doc, 'metadata') and doc.metadata:
                num = doc.metadata.get('num_sumula')
                if num and num not in retrieved_sumulas:
                    retrieved_sumulas.append(str(num))

            if hasattr(doc, 'page_content'):
                context_text_parts.append(doc.page_content)

        hallucination_metadata = {
            "retrieved_sumulas": retrieved_sumulas,
            "context_text": "\n".join(context_text_parts[:5])  # Primeiros 5 docs
        }

        # Adiciona validators avançados (Fase 2)
        validators.extend([
            HallucinationDetection(threshold=0.7, on_fail="reask"),
            ValidSumulaReference(min_sumula=1, max_sumula=200, on_fail="reask")
        ])

    cleaned_text = text
    all_passed = True
    validation_info = []

    for validator in validators:
        # Usa metadata específico para validators da Fase 2
        metadata = {}
        if isinstance(validator, (HallucinationDetection, ValidSumulaReference)):
            metadata = hallucination_metadata

        result = validator.validate(cleaned_text, metadata)

        if result.outcome == "fail":
            all_passed = False
            error_msg = getattr(result, 'error_message', 'Validation failed')
            validation_info.append({
                "validator": validator.__class__.__name__,
                "error": error_msg,
                "metadata": result.metadata if hasattr(result, 'metadata') else {}
            })

            if hasattr(result, 'fixed_value') and result.fixed_value:
                cleaned_text = result.fixed_value

    return {
        "is_valid": all_passed,
        "cleaned_text": cleaned_text,
        "validation_info": validation_info
    }
