"""Dialog for editing a person's social/contact handles."""

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)

from keep_in_touch.domain.models import SOCIAL_PLATFORMS
from keep_in_touch.domain.validation import normalize_socials


class EditSocialsDialog(QDialog):
    """Collect social/contact handles without crowding the main person form."""

    def __init__(self, socials: dict[str, str] | None = None) -> None:
        """Create the dialog with existing handles prefilled."""

        super().__init__()
        self.setWindowTitle("Edit Social Handles")
        self._original_socials = dict(socials or {})
        self.social_edits = {
            platform: QLineEdit(self._original_socials.get(platform, ""))
            for platform, _label in SOCIAL_PLATFORMS
        }

        form = QFormLayout()
        for platform, label in SOCIAL_PLATFORMS:
            form.addRow(label, self.social_edits[platform])

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def socials(self) -> dict[str, str]:
        """Return normalized handles, preserving unknown existing platforms."""

        socials = dict(self._original_socials)
        for platform, edit in self.social_edits.items():
            handle = edit.text().strip()
            if handle:
                socials[platform] = handle
            else:
                socials.pop(platform, None)
        return normalize_socials(socials)
