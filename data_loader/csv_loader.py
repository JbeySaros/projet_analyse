"""
Module de chargement de fichiers CSV avec gestion robuste des erreurs.
Implémente le Repository Pattern pour abstraire l'accès aux données.
"""
import os
from pathlib import Path
from typing import Optional, Union
import pandas as pd
import chardet
from config import settings
from utils.logger import get_logger, PerformanceLogger
from data_loader.exceptions import (
    FileNotFoundError,
    InvalidFileFormatError,
    FileSizeExceededError,
    EmptyFileError,
    EncodingDetectionError,
    CorruptedFileError
)


logger = get_logger(__name__)


class CSVLoader:
    """
    Classe responsable du chargement de fichiers CSV.
    
    Features:
    - Détection automatique de l'encodage
    - Détection automatique du délimiteur
    - Gestion des gros fichiers avec chunking
    - Validation de la taille et du format
    - Logging détaillé des opérations
    
    Example:
        >>> loader = CSVLoader()
        >>> df = loader.load("data/ventes_2025.csv")
        >>> print(df.shape)
    """
    
    COMMON_ENCODINGS = ["utf-8", "utf-8-sig", "latin-1", "iso-8859-1", "cp1252"]
    COMMON_DELIMITERS = [",", ";", "\t", "|"]
    
    def __init__(
        self,
        encoding: Optional[str] = None,
        delimiter: Optional[str] = None,
        chunk_size: Optional[int] = None
    ):
        """
        Initialise le loader avec des paramètres optionnels.
        
        Args:
            encoding: Encodage du fichier (détection auto si None)
            delimiter: Délimiteur CSV (détection auto si None)
            chunk_size: Taille des chunks pour gros fichiers (None = charge tout)
        """
        self.encoding = encoding or settings.CSV_ENCODING
        self.delimiter = delimiter or settings.CSV_DELIMITER
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.auto_detect_encoding = settings.CSV_AUTO_DETECT_ENCODING and not encoding
        self.auto_detect_delimiter = settings.CSV_AUTO_DETECT_DELIMITER and not delimiter
        
        logger.info(
            f"CSVLoader initialisé - encoding={self.encoding}, "
            f"delimiter={self.delimiter}, chunk_size={self.chunk_size}"
        )
    
    def load(
        self,
        file_path: Union[str, Path],
        use_chunks: bool = False,
        **pandas_kwargs
    ) -> pd.DataFrame:
        """
        Charge un fichier CSV et retourne un DataFrame.
        
        Args:
            file_path: Chemin vers le fichier CSV
            use_chunks: Si True, charge le fichier par chunks (pour gros fichiers)
            **pandas_kwargs: Arguments supplémentaires pour pd.read_csv
            
        Returns:
            pd.DataFrame: Données chargées
            
        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            InvalidFileFormatError: Si le format n'est pas supporté
            FileSizeExceededError: Si la taille dépasse la limite
            EmptyFileError: Si le fichier est vide
            CorruptedFileError: Si le fichier est corrompu
            
        Example:
            >>> loader = CSVLoader()
            >>> df = loader.load("data/ventes_2025.csv")
        """
        file_path = Path(file_path)
        
        with PerformanceLogger(logger, f"load_csv({file_path.name})"):
            # Validations préalables
            self._validate_file_exists(file_path)
            self._validate_file_format(file_path)
            self._validate_file_size(file_path)
            
            # Détection automatique de l'encodage
            if self.auto_detect_encoding:
                detected_encoding = self._detect_encoding(file_path)
                logger.info(f"Encodage détecté: {detected_encoding}")
                encoding = detected_encoding
            else:
                encoding = self.encoding
            
            # Détection automatique du délimiteur
            if self.auto_detect_delimiter:
                detected_delimiter = self._detect_delimiter(file_path, encoding)
                logger.info(f"Délimiteur détecté: '{detected_delimiter}'")
                delimiter = detected_delimiter
            else:
                delimiter = self.delimiter
            
            # Chargement du fichier
            try:
                if use_chunks:
                    df = self._load_in_chunks(
                        file_path, encoding, delimiter, **pandas_kwargs
                    )
                else:
                    df = pd.read_csv(
                        file_path,
                        encoding=encoding,
                        delimiter=delimiter,
                        **pandas_kwargs
                    )
                
                # Vérification que le DataFrame n'est pas vide
                if df.empty:
                    raise EmptyFileError(str(file_path))
                
                logger.info(
                    f"Fichier chargé avec succès: {len(df)} lignes, "
                    f"{len(df.columns)} colonnes"
                )
                logger.debug(f"Colonnes: {list(df.columns)}")
                
                return df
                
            except pd.errors.EmptyDataError:
                raise EmptyFileError(str(file_path))
            except pd.errors.ParserError as e:
                raise CorruptedFileError(str(file_path), str(e))
            except Exception as e:
                logger.error(f"Erreur lors du chargement: {str(e)}", exc_info=True)
                raise CorruptedFileError(str(file_path), str(e))
    
    def _validate_file_exists(self, file_path: Path):
        """Vérifie que le fichier existe."""
        if not file_path.exists():
            logger.error(f"Fichier introuvable: {file_path}")
            raise FileNotFoundError(str(file_path))
    
    def _validate_file_format(self, file_path: Path):
        """Vérifie que le format du fichier est supporté."""
        extension = file_path.suffix.lower().lstrip(".")
        if extension not in settings.ALLOWED_EXTENSIONS:
            logger.error(
                f"Format non supporté: {extension} "
                f"(formats autorisés: {settings.ALLOWED_EXTENSIONS})"
            )
            raise InvalidFileFormatError(str(file_path), settings.ALLOWED_EXTENSIONS)
    
    def _validate_file_size(self, file_path: Path):
        """Vérifie que la taille du fichier ne dépasse pas la limite."""
        file_size = file_path.stat().st_size
        if file_size > settings.MAX_FILE_SIZE:
            logger.error(
                f"Taille de fichier dépassée: {file_size / (1024**2):.2f} MB "
                f"(max: {settings.MAX_FILE_SIZE / (1024**2):.2f} MB)"
            )
            raise FileSizeExceededError(file_size, settings.MAX_FILE_SIZE)
        
        logger.debug(f"Taille du fichier: {file_size / (1024**2):.2f} MB")
    
    def _detect_encoding(self, file_path: Path) -> str:
        """
        Détecte l'encodage du fichier.
        
        Args:
            file_path: Chemin du fichier
            
        Returns:
            str: Encodage détecté
            
        Raises:
            EncodingDetectionError: Si la détection échoue
        """
        logger.debug(f"Détection de l'encodage pour {file_path.name}")
        
        # Méthode 1: Utiliser chardet sur un échantillon
        try:
            with open(file_path, "rb") as f:
                raw_data = f.read(10000)  # Lire les 10k premiers octets
                result = chardet.detect(raw_data)
                
                if result["encoding"] and result["confidence"] > 0.7:
                    logger.debug(
                        f"Encodage détecté par chardet: {result['encoding']} "
                        f"(confiance: {result['confidence']:.2%})"
                    )
                    return result["encoding"]
        except Exception as e:
            logger.warning(f"chardet a échoué: {str(e)}")
        
        # Méthode 2: Tester les encodages communs
        for encoding in self.COMMON_ENCODINGS:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    f.read(1000)  # Essayer de lire quelques lignes
                logger.debug(f"Encodage trouvé par essai: {encoding}")
                return encoding
            except (UnicodeDecodeError, LookupError):
                continue
        
        # Si aucune méthode ne fonctionne
        logger.error("Impossible de détecter l'encodage")
        raise EncodingDetectionError(str(file_path), self.COMMON_ENCODINGS)
    
    def _detect_delimiter(self, file_path: Path, encoding: str) -> str:
        """
        Détecte le délimiteur du CSV.
        
        Args:
            file_path: Chemin du fichier
            encoding: Encodage du fichier
            
        Returns:
            str: Délimiteur détecté
        """
        logger.debug(f"Détection du délimiteur pour {file_path.name}")
        
        try:
            # Lire les premières lignes
            with open(file_path, "r", encoding=encoding) as f:
                sample = "".join([f.readline() for _ in range(5)])
            
            # Utiliser le Sniffer de csv
            import csv
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            
            logger.debug(f"Délimiteur détecté par Sniffer: '{delimiter}'")
            return delimiter
            
        except Exception as e:
            logger.warning(f"Détection automatique échouée: {str(e)}")
            
            # Fallback: compter les occurrences
            delimiter_counts = {d: sample.count(d) for d in self.COMMON_DELIMITERS}
            detected = max(delimiter_counts, key=delimiter_counts.get)
            
            logger.debug(
                f"Délimiteur détecté par comptage: '{detected}' "
                f"(occurrences: {delimiter_counts})"
            )
            return detected
    
    def _load_in_chunks(
        self,
        file_path: Path,
        encoding: str,
        delimiter: str,
        **pandas_kwargs
    ) -> pd.DataFrame:
        """
        Charge un gros fichier par chunks et les concatène.
        
        Args:
            file_path: Chemin du fichier
            encoding: Encodage
            delimiter: Délimiteur
            **pandas_kwargs: Arguments pour pd.read_csv
            
        Returns:
            pd.DataFrame: Données concaténées
        """
        logger.info(f"Chargement par chunks (taille: {self.chunk_size})")
        
        chunks = []
        chunk_iterator = pd.read_csv(
            file_path,
            encoding=encoding,
            delimiter=delimiter,
            chunksize=self.chunk_size,
            **pandas_kwargs
        )
        
        for i, chunk in enumerate(chunk_iterator, 1):
            chunks.append(chunk)
            logger.debug(f"Chunk {i} chargé: {len(chunk)} lignes")
        
        df = pd.concat(chunks, ignore_index=True)
        logger.info(f"Tous les chunks concaténés: {len(df)} lignes totales")
        
        return df


class DataLoaderRepository:
    """
    Repository Pattern pour abstraire l'accès aux différentes sources de données.
    Permet d'ajouter facilement d'autres formats (Excel, JSON, API, etc.).
    """
    
    def __init__(self):
        """Initialise le repository avec les loaders disponibles."""
        self.csv_loader = CSVLoader()
        logger.info("DataLoaderRepository initialisé")
    
    def load_data(
        self,
        file_path: Union[str, Path],
        file_format: Optional[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Charge des données depuis un fichier (format auto-détecté).
        
        Args:
            file_path: Chemin du fichier
            file_format: Format du fichier (auto-détecté si None)
            **kwargs: Arguments pour le loader spécifique
            
        Returns:
            pd.DataFrame: Données chargées
            
        Example:
            >>> repo = DataLoaderRepository()
            >>> df = repo.load_data("data/ventes.csv")
        """
        file_path = Path(file_path)
        
        # Détection du format
        if file_format is None:
            file_format = file_path.suffix.lower().lstrip(".")
        
        logger.info(f"Chargement du fichier: {file_path.name} (format: {file_format})")
        
        # Dispatch vers le loader approprié
        if file_format == "csv":
            return self.csv_loader.load(file_path, **kwargs)
        elif file_format in ["xlsx", "xls"]:
            return self._load_excel(file_path, **kwargs)
        else:
            raise InvalidFileFormatError(str(file_path), settings.ALLOWED_EXTENSIONS)
    
    def _load_excel(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """
        Charge un fichier Excel.
        
        Args:
            file_path: Chemin du fichier
            **kwargs: Arguments pour pd.read_excel
            
        Returns:
            pd.DataFrame: Données chargées
        """
        logger.info(f"Chargement Excel: {file_path.name}")
        
        try:
            df = pd.read_excel(file_path, **kwargs)
            logger.info(f"Excel chargé: {len(df)} lignes, {len(df.columns)} colonnes")
            return df
        except Exception as e:
            logger.error(f"Erreur lors du chargement Excel: {str(e)}", exc_info=True)
            raise CorruptedFileError(str(file_path), str(e))
