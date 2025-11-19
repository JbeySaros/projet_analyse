"""
Module de validation des données chargées.
Vérifie la qualité et la conformité des données avant traitement.
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import pandas as pd
import numpy as np
from config import settings
from utils.logger import get_logger, PerformanceLogger
from data_loader.exceptions import (
    ValidationError,
    MissingColumnsError,
    InvalidDataTypeError,
    ExcessiveMissingValuesError,
    DuplicateRowsError,
    InvalidValueRangeError,
    InsufficientDataError
)


logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """
    Résultat de validation d'un DataFrame.
    
    Attributes:
        is_valid: True si toutes les validations passent
        errors: Liste des erreurs rencontrées
        warnings: Liste des avertissements
        metrics: Métriques de qualité des données
    """
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    metrics: Dict[str, Any]
    
    def __str__(self):
        """Représentation textuelle du résultat."""
        status = "✓ VALIDE" if self.is_valid else "✗ INVALIDE"
        error_msg = f"\nErreurs ({len(self.errors)}):\n  " + "\n  ".join(self.errors) if self.errors else ""
        warning_msg = f"\nAvertissements ({len(self.warnings)}):\n  " + "\n  ".join(self.warnings) if self.warnings else ""
        return f"{status}{error_msg}{warning_msg}"


class DataValidator:
    """
    Classe pour valider la qualité et la conformité des données.
    
    Validations disponibles:
    - Présence des colonnes requises
    - Types de données
    - Valeurs manquantes
    - Doublons
    - Plages de valeurs
    - Taille du dataset
    
    Example:
        >>> validator = DataValidator()
        >>> result = validator.validate(df, required_columns=["date", "prix"])
        >>> if not result.is_valid:
        ...     print(result.errors)
    """
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialise le validateur.
        
        Args:
            strict_mode: Si True, les warnings deviennent des erreurs
        """
        self.strict_mode = strict_mode
        logger.info(f"DataValidator initialisé (strict_mode={strict_mode})")
    
    def validate(
        self,
        df: pd.DataFrame,
        required_columns: Optional[List[str]] = None,
        column_types: Optional[Dict[str, str]] = None,
        check_duplicates: bool = True,
        check_missing: bool = True,
        value_ranges: Optional[Dict[str, tuple]] = None,
        min_rows: Optional[int] = None
    ) -> ValidationResult:
        """
        Valide un DataFrame selon plusieurs critères.
        
        Args:
            df: DataFrame à valider
            required_columns: Liste des colonnes obligatoires
            column_types: Dict {colonne: type_attendu}
            check_duplicates: Vérifier les doublons
            check_missing: Vérifier les valeurs manquantes
            value_ranges: Dict {colonne: (min, max)} pour vérifier les plages
            min_rows: Nombre minimum de lignes requises
            
        Returns:
            ValidationResult: Résultat de la validation
            
        Example:
            >>> result = validator.validate(
            ...     df,
            ...     required_columns=["date", "prix", "quantite"],
            ...     column_types={"prix": "float", "quantite": "int"},
            ...     value_ranges={"prix": (0, None), "quantite": (1, None)}
            ... )
        """
        with PerformanceLogger(logger, "validate_dataframe"):
            errors = []
            warnings = []
            metrics = self._calculate_metrics(df)
            
            logger.info(f"Validation d'un DataFrame: {df.shape[0]} lignes, {df.shape[1]} colonnes")
            
            # Validation 1: Colonnes requises
            if required_columns:
                try:
                    self._validate_required_columns(df, required_columns)
                    logger.debug("Colonnes requises présentes")
                except MissingColumnsError as e:
                    errors.append(str(e))
                    logger.error(f"{str(e)}")
            
            # Validation 2: Types de données
            if column_types:
                type_errors = self._validate_column_types(df, column_types)
                if type_errors:
                    errors.extend(type_errors)
                    logger.error(f"{len(type_errors)} erreurs de type")
                else:
                    logger.debug("Types de données valides")
            
            # Validation 3: Valeurs manquantes
            if check_missing:
                missing_warnings = self._check_missing_values(df)
                if missing_warnings:
                    if self.strict_mode:
                        errors.extend(missing_warnings)
                    else:
                        warnings.extend(missing_warnings)
                    logger.warning(f"{len(missing_warnings)} colonnes avec valeurs manquantes")
                else:
                    logger.debug("Aucune valeur manquante")
            
            # Validation 4: Doublons
            if check_duplicates:
                try:
                    self._check_duplicates(df)
                    logger.debug("Aucun doublon détecté")
                except DuplicateRowsError as e:
                    if self.strict_mode:
                        errors.append(str(e))
                    else:
                        warnings.append(str(e))
                    logger.warning(f"{str(e)}")
            
            # Validation 5: Plages de valeurs
            if value_ranges:
                range_errors = self._validate_value_ranges(df, value_ranges)
                if range_errors:
                    errors.extend(range_errors)
                    logger.error(f"{len(range_errors)} erreurs de plage")
                else:
                    logger.debug("Plages de valeurs respectées")
            
            # Validation 6: Nombre de lignes
            if min_rows:
                try:
                    self._validate_min_rows(df, min_rows)
                    logger.debug(f"Nombre de lignes suffisant (>= {min_rows})")
                except InsufficientDataError as e:
                    errors.append(str(e))
                    logger.error(f"{str(e)}")
            
            # Résultat final
            is_valid = len(errors) == 0
            result = ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                metrics=metrics
            )
            
            if is_valid:
                logger.info("Validation réussie")
            else:
                logger.error(f"Validation échouée: {len(errors)} erreur(s)")
            
            return result
    
    def _validate_required_columns(self, df: pd.DataFrame, required_columns: List[str]):
        """Vérifie que toutes les colonnes requises sont présentes."""
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise MissingColumnsError(missing, list(df.columns))
    
    def _validate_column_types(
        self,
        df: pd.DataFrame,
        column_types: Dict[str, str]
    ) -> List[str]:
        """
        Vérifie les types de données des colonnes.
        
        Returns:
            List[str]: Liste des erreurs de type
        """
        errors = []
        
        type_mapping = {
            "int": ["int64", "int32", "int16", "int8"],
            "float": ["float64", "float32", "int64", "int32"],  # int accepté pour float
            "str": ["object"],
            "string": ["object"],
            "datetime": ["datetime64[ns]"],
            "bool": ["bool"],
            "category": ["category"]
        }
        
        for column, expected_type in column_types.items():
            if column not in df.columns:
                continue
            
            actual_type = str(df[column].dtype)
            expected_dtypes = type_mapping.get(expected_type, [expected_type])
            
            if actual_type not in expected_dtypes:
                errors.append(
                    f"Type invalide pour '{column}': "
                    f"attendu {expected_type}, obtenu {actual_type}"
                )
        
        return errors
    
    def _check_missing_values(self, df: pd.DataFrame) -> List[str]:
        """
        Vérifie les valeurs manquantes dans chaque colonne.
        
        Returns:
            List[str]: Warnings pour les colonnes avec trop de valeurs manquantes
        """
        warnings = []
        threshold = settings.MAX_MISSING_PERCENTAGE
        
        for column in df.columns:
            missing_count = df[column].isna().sum()
            if missing_count > 0:
                missing_pct = (missing_count / len(df)) * 100
                
                if missing_pct > threshold * 100:
                    warnings.append(
                        f"Colonne '{column}': {missing_pct:.1f}% de valeurs manquantes "
                        f"({missing_count}/{len(df)}) - seuil: {threshold*100}%"
                    )
        
        return warnings
    
    def _check_duplicates(self, df: pd.DataFrame):
        """Vérifie la présence de lignes dupliquées."""
        duplicate_count = df.duplicated().sum()
        if duplicate_count > 0:
            raise DuplicateRowsError(int(duplicate_count), len(df))
    
    def _validate_value_ranges(
        self,
        df: pd.DataFrame,
        value_ranges: Dict[str, tuple]
    ) -> List[str]:
        """
        Vérifie que les valeurs sont dans les plages autorisées.
        
        Args:
            value_ranges: Dict {colonne: (min, max)}
                         Utilisez None pour pas de limite
        
        Returns:
            List[str]: Liste des erreurs de plage
        """
        errors = []
        
        for column, (min_val, max_val) in value_ranges.items():
            if column not in df.columns:
                continue
            
            # Ignorer les NaN pour cette validation
            valid_data = df[column].dropna()
            
            if len(valid_data) == 0:
                continue
            
            invalid_count = 0
            
            if min_val is not None:
                invalid_count += (valid_data < min_val).sum()
            
            if max_val is not None:
                invalid_count += (valid_data > max_val).sum()
            
            if invalid_count > 0:
                errors.append(
                    f"Colonne '{column}': {invalid_count} valeurs hors limites "
                    f"(min={min_val}, max={max_val})"
                )
        
        return errors
    
    def _validate_min_rows(self, df: pd.DataFrame, min_rows: int):
        """Vérifie que le DataFrame contient assez de lignes."""
        if len(df) < min_rows:
            raise InsufficientDataError(len(df), min_rows)
    
    def _calculate_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calcule des métriques de qualité sur le DataFrame.
        
        Returns:
            Dict: Métriques (shape, memory, missing_pct, etc.)
        """
        total_cells = df.shape[0] * df.shape[1]
        missing_cells = df.isna().sum().sum()
        
        metrics = {
            "n_rows": int(df.shape[0]),
            "n_columns": int(df.shape[1]),
            "total_cells": int(total_cells),
            "missing_cells": int(missing_cells),
            "missing_percentage": float(missing_cells / total_cells * 100) if total_cells > 0 else 0.0,
            "duplicate_rows": int(df.duplicated().sum()),
            "memory_usage_mb": float(df.memory_usage(deep=True).sum() / (1024**2)),
            "column_types": df.dtypes.astype(str).to_dict()
        }
        
        return metrics
    
    def validate_sales_data(self, df: pd.DataFrame) -> ValidationResult:
        """
        Validation spécifique pour les données de ventes.
        Règles métier pour le fichier vente_2025.csv.
        
        Args:
            df: DataFrame de ventes
            
        Returns:
            ValidationResult: Résultat de validation
            
        Example:
            >>> validator = DataValidator()
            >>> result = validator.validate_sales_data(df)
        """
        logger.info("Validation des données de ventes")
        
        return self.validate(
            df,
            required_columns=["date", "produit", "categorie", "prix", "quantite", "ville", "source"],
            column_types={
                "date": "object",
                "produit": "str",
                "categorie": "str",
                "prix": "float",
                "quantite": "int",
                "ville": "str",
                "source": "str"
            },
            check_duplicates=True,
            check_missing=True,
            value_ranges={
                "prix": (0, None),  # Prix doit être positif
                "quantite": (1, None)  # Quantité doit être >= 1
            },
            min_rows=settings.MIN_DATA_ROWS
        )


class ValidationSchema:
    """
    Classe pour définir des schémas de validation réutilisables.
    Pattern Strategy pour différents types de données.
    """
    
    @staticmethod
    def sales_schema() -> dict:
        """Schéma de validation pour les données de ventes."""
        return {
            "required_columns": ["date", "produit", "categorie", "prix", "quantite", "ville", "source"],
            "column_types": {
                "prix": "float",
                "quantite": "int"
            },
            "value_ranges": {
                "prix": (0, None),
                "quantite": (1, None)
            }
        }
    
    @staticmethod
    def customer_schema() -> dict:
        """Schéma de validation pour les données clients."""
        return {
            "required_columns": ["customer_id", "name", "email"],
            "column_types": {
                "customer_id": "int"
            }
        }
