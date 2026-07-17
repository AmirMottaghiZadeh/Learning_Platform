from django import forms
from django.core.exceptions import ValidationError

from apps.ai_data_pipeline import constants
from apps.ai_data_pipeline.models import AIDataBatch, AIDataJob, AIDataSuggestion
from apps.drugs.models import Drug


class SuggestionFilterForm(forms.Form):
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={"placeholder": "Search suggestions"}))
    batch = forms.ModelChoiceField(required=False, queryset=AIDataBatch.objects.order_by("-created_at"))
    provider = forms.ChoiceField(required=False, choices=[("", "All providers"), *[(item, item) for item in sorted(constants.PROVIDER_CHOICES)]])
    status = forms.ChoiceField(required=False, choices=[("", "All statuses"), *AIDataSuggestion.STATUS_CHOICES])
    risk_level = forms.ChoiceField(required=False, choices=[("", "All risk levels"), *AIDataSuggestion.RISK_CHOICES])
    suggestion_type = forms.CharField(required=False)
    table_name = forms.CharField(required=False)
    field_name = forms.CharField(required=False)
    sort = forms.ChoiceField(
        required=False,
        choices=[
            ("-created_at", "Newest"),
            ("created_at", "Oldest"),
            ("-confidence_score", "Highest confidence"),
            ("confidence_score", "Lowest confidence"),
        ],
        initial="-created_at",
    )


class SuggestionEditForm(forms.Form):
    suggested_value = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 5}))
    reason = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 4}))
    confidence_score = forms.FloatField(required=False, min_value=0, max_value=1)
    risk_level = forms.ChoiceField(required=False, choices=AIDataSuggestion.RISK_CHOICES)
    reviewer_notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def clean_confidence_score(self):
        value = self.cleaned_data.get("confidence_score")
        if value is None:
            return value
        return float(value)


class SuggestionReviewActionForm(forms.Form):
    action = forms.ChoiceField(
        choices=[
            ("approve", "Approve"),
            ("reject", "Reject"),
            ("edit", "Edit before approval"),
        ]
    )
    reviewer_notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
    selected_ids = forms.CharField(required=False, widget=forms.HiddenInput())


class RuleBasedSuggestionBatchForm(forms.Form):
    batch_name = forms.CharField(
        required=False,
        max_length=120,
        label="Package name",
        widget=forms.TextInput(attrs={"placeholder": "e.g. July normalization review"}),
    )
    max_suggestions = forms.IntegerField(
        min_value=1,
        max_value=2000,
        initial=500,
        label="Maximum suggestions",
        help_text="The review package stops after this many suggestions are created.",
    )
    include_normalization = forms.BooleanField(
        required=False,
        initial=True,
        label="Normalization rules",
        help_text="Safe spacing, Persian-character, punctuation, and casing fixes.",
    )
    include_terminology = forms.BooleanField(
        required=False,
        initial=True,
        label="Terminology rules",
        help_text="Safe configured terminology and dosage/unit standardization.",
    )
    include_medical_validation = forms.BooleanField(
        required=False,
        label="Medical validation warnings",
        help_text="Review-only warnings; they are never automatically applied.",
    )
    include_duplicates = forms.BooleanField(
        required=False,
        label="Duplicate candidates",
        help_text="Review-only duplicate candidates; they are never automatically applied.",
    )
    include_translations = forms.BooleanField(
        required=False,
        label="Translation metadata suggestions",
        help_text="Creates translation metadata suggestions, not direct drug-field updates.",
    )

    def clean(self):
        cleaned_data = super().clean()
        rule_options = (
            "include_normalization",
            "include_terminology",
            "include_medical_validation",
            "include_duplicates",
            "include_translations",
        )
        if not any(cleaned_data.get(option) for option in rule_options):
            raise ValidationError("Select at least one rule group for the review package.")
        return cleaned_data


class BatchFilterForm(forms.Form):
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={"placeholder": "Search batches"}))
    batch_type = forms.ChoiceField(required=False, choices=[("", "All types"), *AIDataBatch.BATCH_TYPE_CHOICES])
    status = forms.ChoiceField(required=False, choices=[("", "All statuses"), *AIDataBatch.STATUS_CHOICES])
    created_by = forms.CharField(required=False)


class JobFilterForm(forms.Form):
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={"placeholder": "Search jobs"}))
    job_type = forms.ChoiceField(required=False, choices=[("", "All jobs"), *AIDataJob.JOB_TYPE_CHOICES])
    status = forms.ChoiceField(required=False, choices=[("", "All statuses"), ("pending", "Pending"), ("running", "Running"), ("completed", "Completed"), ("failed", "Failed"), ("cancelled", "Cancelled")])
    provider = forms.ChoiceField(required=False, choices=[("", "All providers"), *[(item, item) for item in sorted(constants.PROVIDER_CHOICES)]])


class DrugDatabaseFilterForm(forms.Form):
    SEARCH_FIELD_CHOICES = [
        ("all", "All searchable fields"),
        ("name", "Name"),
        ("persian_name", "Persian name"),
        ("brand_name", "Brand name"),
        ("generic_name", "Generic name"),
        ("indication", "Indication"),
        ("indication_answer", "Indication answer"),
        ("side_effects", "Side effects"),
        ("side_effects_answer", "Side effects answer"),
        ("dosage_form", "Dosage form"),
        ("drug_classification", "Classification"),
        ("consumption_time", "Consumption time"),
        ("consumption_time_sorted", "Consumption time (normalized)"),
        ("dosing_and_administration", "Dosing and administration"),
        ("pregnancy", "Pregnancy"),
        ("breastfeeding", "Breastfeeding"),
        ("dose_adjustment", "Dose adjustment"),
        ("clinical_notes", "Clinical notes"),
        ("source_topic", "Source topic"),
    ]

    q = forms.CharField(required=False, label="Search", widget=forms.TextInput(attrs={"placeholder": "Search drug information"}))
    search_field = forms.ChoiceField(required=False, label="Search in", choices=SEARCH_FIELD_CHOICES, initial="all")
    sort = forms.ChoiceField(
        required=False,
        choices=[
            ("generic_name", "Generic name"),
            ("brand_name", "Brand name"),
            ("-updated_at", "Recently updated"),
            ("-created_at", "Recently added"),
        ],
        initial="generic_name",
    )


class DrugDatabaseEditForm(forms.ModelForm):
    JSON_LIST_FIELDS = ("atc_codes", "atc_classes", "atc_subclasses", "atc_categories", "category")

    class Meta:
        model = Drug
        fields = [
            "name",
            "persian_name",
            "brand_name",
            "generic_name",
            "dosage_form",
            "drug_classification",
            "consumption_time",
            "consumption_time_sorted",
            "indication",
            "indication_answer",
            "side_effects",
            "side_effects_answer",
            "dosing_and_administration",
            "pregnancy",
            "breastfeeding",
            "dose_adjustment",
            "clinical_notes",
            "atc_codes",
            "atc_classes",
            "atc_subclasses",
            "atc_categories",
            "category",
            "source_topic",
            "extra_attributes",
        ]
        labels = {
            "name": "Name",
            "persian_name": "Persian name",
            "brand_name": "Brand name",
            "generic_name": "Generic name",
            "dosage_form": "Dosage form",
            "drug_classification": "Classification",
            "consumption_time": "Consumption time",
            "consumption_time_sorted": "Consumption time (normalized)",
            "indication": "Indication",
            "indication_answer": "Indication answer",
            "side_effects": "Side effects",
            "side_effects_answer": "Side effects answer",
            "dosing_and_administration": "Dosing and administration",
            "pregnancy": "Pregnancy",
            "breastfeeding": "Breastfeeding",
            "dose_adjustment": "Dose adjustment",
            "clinical_notes": "Clinical notes",
            "atc_codes": "ATC codes (JSON)",
            "atc_classes": "ATC classes (JSON)",
            "atc_subclasses": "ATC subclasses (JSON)",
            "atc_categories": "ATC categories (JSON)",
            "category": "Categories (JSON)",
            "source_topic": "Source topic",
            "extra_attributes": "Extra attributes (JSON)",
        }
        widgets = {
            "name": forms.TextInput(),
            "persian_name": forms.TextInput(),
            "brand_name": forms.Textarea(attrs={"rows": 3}),
            "generic_name": forms.Textarea(attrs={"rows": 3}),
            "dosage_form": forms.Textarea(attrs={"rows": 3}),
            "drug_classification": forms.Textarea(attrs={"rows": 3}),
            "consumption_time": forms.Textarea(attrs={"rows": 3}),
            "consumption_time_sorted": forms.Textarea(attrs={"rows": 3}),
            "indication": forms.Textarea(attrs={"rows": 5}),
            "indication_answer": forms.Textarea(attrs={"rows": 5}),
            "side_effects": forms.Textarea(attrs={"rows": 5}),
            "side_effects_answer": forms.Textarea(attrs={"rows": 5}),
            "dosing_and_administration": forms.Textarea(attrs={"rows": 5}),
            "pregnancy": forms.Textarea(attrs={"rows": 4}),
            "breastfeeding": forms.Textarea(attrs={"rows": 4}),
            "dose_adjustment": forms.Textarea(attrs={"rows": 4}),
            "clinical_notes": forms.Textarea(attrs={"rows": 5}),
            "atc_codes": forms.Textarea(attrs={"rows": 3}),
            "atc_classes": forms.Textarea(attrs={"rows": 3}),
            "atc_subclasses": forms.Textarea(attrs={"rows": 3}),
            "atc_categories": forms.Textarea(attrs={"rows": 3}),
            "category": forms.Textarea(attrs={"rows": 3}),
            "source_topic": forms.TextInput(),
            "extra_attributes": forms.Textarea(attrs={"rows": 6}),
        }

    def clean(self):
        cleaned_data = super().clean()
        for field_name in self.JSON_LIST_FIELDS:
            if cleaned_data.get(field_name) is None:
                cleaned_data[field_name] = []
        if cleaned_data.get("extra_attributes") is None:
            cleaned_data["extra_attributes"] = {}
        return cleaned_data


class DrugDatabaseCreateForm(DrugDatabaseEditForm):
    def clean(self):
        cleaned_data = super().clean()
        identity_fields = ("name", "persian_name", "brand_name", "generic_name")
        if not any(str(cleaned_data.get(field_name, "")).strip() for field_name in identity_fields):
            raise ValidationError(
                "Provide at least one identifying name: name, Persian name, brand name, or generic name."
            )
        return cleaned_data


class DrugDatabaseDeleteForm(forms.Form):
    confirmation = forms.CharField(
        label="Deletion confirmation",
        help_text='Type DELETE exactly to permanently remove this drug record.',
        widget=forms.TextInput(attrs={"autocomplete": "off", "placeholder": "DELETE"}),
    )

    def clean_confirmation(self):
        confirmation = self.cleaned_data["confirmation"].strip()
        if confirmation != "DELETE":
            raise ValidationError("Type DELETE exactly to confirm this operation.")
        return confirmation
