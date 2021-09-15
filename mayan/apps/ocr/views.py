from __future__ import absolute_import, unicode_literals

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _, ungettext

from mayan.apps.common.generics import (
    FormView, MultipleObjectConfirmActionView, SingleObjectDetailView,
    SingleObjectDownloadView, SingleObjectEditView, SingleObjectListView
)
from mayan.apps.documents.forms import DocumentTypeFilteredSelectForm
from mayan.apps.documents.models import Document, DocumentPage, DocumentType

from .forms import DocumentPageOCRContentForm, DocumentOCRContentForm
from .models import DocumentVersionOCRError
from .permissions import (
    permission_ocr_content_view, permission_ocr_document,
    permission_document_type_ocr_setup
)
from .utils import get_document_content_iterator


class DocumentOCRContentView(SingleObjectDetailView):
    form_class = DocumentOCRContentForm
    model = Document
    object_permission = permission_ocr_content_view

    def dispatch(self, request, *args, **kwargs):
        result = super(DocumentOCRContentView, self).dispatch(
            request, *args, **kwargs
        )
        self.get_object().add_as_recent_document_for_user(user=request.user)
        return result

    def get_extra_context(self):
        return {
            'document': self.get_object(),
            'hide_labels': True,
            'object': self.get_object(),
            'title': _('OCR result for document: %s') % self.get_object(),
        }


class DocumentOCRDownloadView(SingleObjectDownloadView):
    model = Document
    object_permission = permission_ocr_content_view

    def get_file(self):
        file_object = DocumentOCRDownloadView.TextIteratorIO(
            iterator=get_document_content_iterator(document=self.get_object())
        )
        return DocumentOCRDownloadView.VirtualFile(
            file=file_object, name='{}-OCR'.format(self.get_object())
        )


class DocumentOCRErrorsListView(SingleObjectListView):
    object_permission = permission_ocr_document

    def get_document(self):
        return get_object_or_404(klass=Document, pk=self.kwargs['pk'])

    def get_extra_context(self):
        return {
            'hide_object': True,
            'object': self.get_document(),
            'title': _('OCR errors for document: %s') % self.get_document(),
        }

    def get_object_list(self):
        return self.get_document().latest_version.ocr_errors.all()


class DocumentPageOCRContentView(SingleObjectDetailView):
    form_class = DocumentPageOCRContentForm
    model = DocumentPage
    object_permission = permission_ocr_content_view

    def dispatch(self, request, *args, **kwargs):
        result = super(DocumentPageOCRContentView, self).dispatch(
            request, *args, **kwargs
        )
        self.get_object().document.add_as_recent_document_for_user(
            user=request.user
        )
        return result

    def get_extra_context(self):
        return {
            'hide_labels': True,
            'object': self.get_object(),
            'title': _('OCR result for document page: %s') % self.get_object(),
        }


class DocumentSubmitView(MultipleObjectConfirmActionView):
    model = Document
    object_permission = permission_ocr_document
    success_message = '%(count)d document submitted to the OCR queue.'
    success_message_plural = '%(count)d documents submitted to the OCR queue.'

    def get_extra_context(self):
        queryset = self.get_queryset()

        result = {
            'title': ungettext(
                'Submit the selected document to the OCR queue?',
                'Submit the selected documents to the OCR queue?',
                queryset.count()
            )
        }

        return result

    def object_action(self, form, instance):
        instance.submit_for_ocr()


class DocumentTypeSettingsEditView(SingleObjectEditView):
    fields = ('auto_ocr',)
    object_permission = permission_document_type_ocr_setup
    post_action_redirect = reverse_lazy('documents:document_type_list')

    def get_document_type(self):
        return get_object_or_404(klass=DocumentType, pk=self.kwargs['pk'])

    def get_extra_context(self):
        return {
            'object': self.get_document_type(),
            'title': _(
                'Edit OCR settings for document type: %s'
            ) % self.get_document_type()
        }

    def get_object(self, queryset=None):
        return self.get_document_type().ocr_settings


class DocumentTypeSubmitView(FormView):
    extra_context = {
        'title': _('Submit all documents of a type for OCR')
    }
    form_class = DocumentTypeFilteredSelectForm
    post_action_redirect = reverse_lazy('common:tools_list')

    def get_form_extra_kwargs(self):
        return {
            'allow_multiple': True,
            'permission': permission_ocr_document,
            'user': self.request.user
        }

    def form_valid(self, form):
        count = 0
        for document_type in form.cleaned_data['document_type']:
            for document in document_type.documents.all():
                document.submit_for_ocr()
                count += 1

        messages.success(
            self.request, _(
                '%(count)d documents added to the OCR queue.'
            ) % {
                'count': count,
            }
        )

        return HttpResponseRedirect(self.get_success_url())


class EntryListView(SingleObjectListView):
    extra_context = {
        'hide_object': True,
        'title': _('OCR errors'),
    }
    view_permission = permission_document_type_ocr_setup

    def get_object_list(self):
        return DocumentVersionOCRError.objects.all()
