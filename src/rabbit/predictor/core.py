import contextlib
import io
from dataclasses import dataclass, field
from importlib.resources import files
import logging

from ghmap.mapping.activity_mapper import ActivityMapper
from ghmap.mapping.action_mapper import ActionMapper
from ghmap.utils import load_json_file

from .features import ActivityFeatureExtractor
from .models import Predictor

logger = logging.getLogger(__name__)


@dataclass
class ContributorResult:
    """
    Dataclass to hold the result of a contributor prediction

    Attributes:
        contributor: The GitHub username of the analyzed contributor.
        user_type: The predicted classification. Must be one of:
            - "Bot": Predicted to be an automated account
            - "Human": Predicted to be a human user
            - "Unknown": Insufficient data for prediction
            - "Invalid": Processing error (e.g., user not found)
        confidence: Prediction confidence score (0.0-1.0), or "-" if unavailable.
        features: Dictionary of computed behavioral features (38 features from
            FEATURE_NAMES). Empty dict if prediction was not made.
    """

    contributor: str
    user_type: str = "Unknown"
    confidence: float | str = "-"
    features: dict[str, float] = field(default_factory=dict)

    def __str__(self):
        """Return a CSV representation of the result without features."""
        return f"{self.contributor},{self.user_type},{self.confidence}"


def compute_activity_sequences(events: list[dict]) -> list[dict]:
    """
    Compute activity sequences from the given events using the ghmap tool.

    Args:
        events (list[dict]): List of event records
    Returns:
        list: List[dict] of activity sequences computed using ghmap
    """
    # Suppress ghmap stdout output
    stdout_capture = io.StringIO()
    with contextlib.redirect_stdout(stdout_capture):
        action_mapping_file = files("ghmap").joinpath("config", "event_to_action.json")
        action_mapping_json = load_json_file(action_mapping_file)
        action_mapper = ActionMapper(action_mapping_json, progress_bar=False)
        actions = action_mapper.map(events)
        logger.debug(f"Mapped {len(events)} events to {len(actions)} actions.")

        activity_mapping_file = files("ghmap").joinpath(
            "config", "action_to_activity.json"
        )
        action_mapping_json = load_json_file(activity_mapping_file)
        activity_mapper = ActivityMapper(action_mapping_json, progress_bar=False)
        activities = activity_mapper.map(actions)
        logger.debug(f"Mapped {len(actions)} actions to {len(activities)} activities.")
    captured_output = stdout_capture.getvalue()
    if captured_output:
        # Filter output to keep only relevant debug info ("Warning: unused actions" and {actions})
        text = ""
        for line in captured_output.splitlines():
            if "Warning: Unused actions" in line:
                # Keep only the part of the line after the warning
                line = line[line.index("Warning: Unused actions") :]
                text += line + "\n"

        if text:
            logger.debug("ghmap output: %s", text.strip())

    return activities


def predict_user_type(
    username: str, events: list, predictor: Predictor
) -> ContributorResult:
    """
    Classify a contributor as bot or human using their GitHub events.

    This function is useful when you have already collected GitHub event data
    and want to perform classification without using the GitHub API extractor.
    It handles the full pipeline: event transformation, feature extraction,
    and prediction.

    Args:
        username: GitHub username of the contributor to analyze.
        events: List of GitHub event dictionaries (raw API response format).
            Must contain at least 'type', 'actor', 'repo', and 'created_at'.
        predictor: Loaded prediction model (e.g., ONNXPredictor instance).

    Returns:
        ContributorResult containing the classification, confidence score,
        and computed features.

    Raises:
        ValueError: If events contain data for multiple contributors.

    Example:
        >>> events = [
        >>>     {"type": "PushEvent", "actor": {"login": "alice"},
        >>>      "repo": {"id": 123, "name": "owner/repo"},
        >>>      "created_at": "2024-01-01T10:00:00Z"}
        >>> ]
        >>> predictor = ONNXPredictor()
        >>> result = predict_user_type("alice", events, predictor)
        >>> print(f"{result.user_type}: {result.confidence}")
        Human: 0.872
    """
    activities = compute_activity_sequences(events)
    if len(activities) == 0:
        # Events where found but no activities could be computed
        logger.debug("No activity sequences found for user %s", username)
        return ContributorResult(username, "Unknown", "-")

    feature_extractor = ActivityFeatureExtractor(username, activities)
    features_df = feature_extractor.compute_features()

    user_type, confidence = predictor.predict(features_df)

    features_dict = features_df.iloc[0].to_dict() if not features_df.empty else {}
    return ContributorResult(username, user_type, confidence, features_dict)
