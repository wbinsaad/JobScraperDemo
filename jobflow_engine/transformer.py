from typing import Any

from logger import get_logger
from models import FieldMappingRule

logger = get_logger(__name__)

class JobTransformationError(Exception):
    """Raised when a raw job cannot be transformed into canonical format."""


class JobTransformer:
    """
    Mapping-driven transformer.
    """

    def transform(
        self,
        source: str,
        raw_job: dict[str, Any],
        field_mapping: dict[str, FieldMappingRule],
    ) -> dict[str, Any]:
        canonical_job: dict[str, Any] = {
            "source": source,
        }

        for canonical_field, rule in field_mapping.items():
            canonical_job[canonical_field] = self._extract_value(
                raw_job=raw_job,
                canonical_field=canonical_field,
                rule=rule,
            )

        return canonical_job

    def _extract_value(
        self,
        raw_job: dict[str, Any],
        canonical_field: str,
        rule: FieldMappingRule,
    ) -> Any:
        value: Any = raw_job

        for key in rule.path.split("."):
            if not isinstance(value, dict):
                if rule.required:
                    raise JobTransformationError(
                        f"Cannot map '{canonical_field}' from '{rule.path}' because '{key}' is not inside an object"
                    )

                return rule.default

            if key not in value:
                if rule.required:
                    raise JobTransformationError(
                        f"Missing required raw field for '{canonical_field}': {rule.path}"
                    )

                return rule.default

            value = value[key]

        if value is None and not rule.required:
            return rule.default

        if value is None and rule.required:
            raise JobTransformationError(
                f"Required raw field for '{canonical_field}' is null: {rule.path}"
            )

        return value