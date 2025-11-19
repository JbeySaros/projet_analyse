"""
Exceptions personnalisées pour la couche data_loader.
Permet une gestion d'erreurs fine et des messages explicites.
"""


class DataLoaderException(Exception):
    """Exception de base pour tous les problèmes de chargement de données."""
    
    def __init__(self, message: str, details: dict = None):
        """
        Initialise l'exception avec un message et des détails optionnels.
        
        Args:
            message: Message d'erreur principal
            details: Dictionnaire avec des détails supplémentaires
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        """Représentation textuelle de l'exception."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} [{details_str}]"
        return self.message


class FileNotFoundError(DataLoaderException):
    """Levée quand le fichier spécifié n'existe pas."""
    
    def __init__(self, file_path: str):
        super().__init__(
            f"Fichier introuvable: {file_path}",
            {"file_path": file_path}
        )


class InvalidFileFormatError(DataLoaderException):
    """Levée quand le format de fichier n'est pas supporté."""
    
    def __init__(self, file_path: str, allowed_formats: set):
        super().__init__(
            f"Format de fichier non supporté: {file_path}",
            {
                "file_path": file_path,
                "allowed_formats": list(allowed_formats)
            }
        )


class FileSizeExceededError(DataLoaderException):
    """Levée quand la taille du fichier dépasse la limite."""
    
    def __init__(self, file_size: int, max_size: int):
        super().__init__(
            f"Taille de fichier dépassée: {file_size / (1024**2):.2f} MB "
            f"(max: {max_size / (1024**2):.2f} MB)",
            {"file_size": file_size, "max_size": max_size}
        )


class EmptyFileError(DataLoaderException):
    """Levée quand le fichier est vide ou ne contient pas de données."""
    
    def __init__(self, file_path: str):
        super().__init__(
            f"Fichier vide ou sans données: {file_path}",
            {"file_path": file_path}
        )


class EncodingDetectionError(DataLoaderException):
    """Levée quand l'encodage du fichier ne peut être détecté."""
    
    def __init__(self, file_path: str, attempted_encodings: list):
        super().__init__(
            f"Impossible de détecter l'encodage du fichier: {file_path}",
            {
                "file_path": file_path,
                "attempted_encodings": attempted_encodings
            }
        )


class CorruptedFileError(DataLoaderException):
    """Levée quand le fichier est corrompu ou malformé."""
    
    def __init__(self, file_path: str, error_details: str):
        super().__init__(
            f"Fichier corrompu ou malformé: {file_path}",
            {"file_path": file_path, "error": error_details}
        )


class ValidationError(DataLoaderException):
    """Exception de base pour les erreurs de validation."""
    pass


class MissingColumnsError(ValidationError):
    """Levée quand des colonnes requises sont manquantes."""
    
    def __init__(self, missing_columns: list, found_columns: list):
        super().__init__(
            f"Colonnes manquantes: {missing_columns}",
            {
                "missing_columns": missing_columns,
                "found_columns": found_columns
            }
        )


class InvalidDataTypeError(ValidationError):
    """Levée quand une colonne a un type de données invalide."""
    
    def __init__(self, column: str, expected_type: str, actual_type: str):
        super().__init__(
            f"Type de données invalide pour la colonne '{column}': "
            f"attendu {expected_type}, obtenu {actual_type}",
            {
                "column": column,
                "expected_type": expected_type,
                "actual_type": actual_type
            }
        )


class ExcessiveMissingValuesError(ValidationError):
    """Levée quand une colonne a trop de valeurs manquantes."""
    
    def __init__(self, column: str, missing_pct: float, threshold: float):
        super().__init__(
            f"Colonne '{column}' contient {missing_pct:.1f}% de valeurs manquantes "
            f"(seuil: {threshold:.1f}%)",
            {
                "column": column,
                "missing_percentage": missing_pct,
                "threshold": threshold
            }
        )


class DuplicateRowsError(ValidationError):
    """Levée quand des doublons sont détectés."""
    
    def __init__(self, duplicate_count: int, total_rows: int):
        super().__init__(
            f"{duplicate_count} lignes dupliquées détectées sur {total_rows} lignes totales",
            {
                "duplicate_count": duplicate_count,
                "total_rows": total_rows,
                "duplicate_percentage": (duplicate_count / total_rows * 100)
            }
        )


class InvalidValueRangeError(ValidationError):
    """Levée quand des valeurs sont hors de la plage autorisée."""
    
    def __init__(
        self,
        column: str,
        invalid_count: int,
        min_value=None,
        max_value=None
    ):
        range_msg = ""
        if min_value is not None and max_value is not None:
            range_msg = f"entre {min_value} et {max_value}"
        elif min_value is not None:
            range_msg = f"≥ {min_value}"
        elif max_value is not None:
            range_msg = f"≤ {max_value}"
        
        super().__init__(
            f"{invalid_count} valeurs invalides dans la colonne '{column}' "
            f"(plage attendue: {range_msg})",
            {
                "column": column,
                "invalid_count": invalid_count,
                "min_value": min_value,
                "max_value": max_value
            }
        )


class InsufficientDataError(ValidationError):
    """Levée quand le jeu de données contient trop peu de lignes."""
    
    def __init__(self, row_count: int, min_required: int):
        super().__init__(
            f"Données insuffisantes: {row_count} lignes "
            f"(minimum requis: {min_required})",
            {
                "row_count": row_count,
                "min_required": min_required
            }
        )
