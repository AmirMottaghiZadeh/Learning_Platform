from django import forms

from apps.ai_data_pipeline import constants
from apps.ai_data_pipeline.models import AIDataBatch, AIDataJob, AIDataSuggestion


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
