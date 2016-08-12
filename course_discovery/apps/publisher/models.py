import logging

from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from django_fsm import FSMField, transition
from simple_history.models import HistoricalRecords
from sortedm2m.fields import SortedManyToManyField

from course_discovery.apps.core.models import User, Currency
from course_discovery.apps.course_metadata.models import LevelType, Subject, Person, Organization
from course_discovery.apps.course_metadata.models import CourseRun as CourseMetadataCourseRun
from course_discovery.apps.ietf_language_tags.models import LanguageTag

logger = logging.getLogger(__name__)


class ChangedByMixin(object):
    changed_by = models.ForeignKey(User, null=True, blank=True)


class State(TimeStampedModel, ChangedByMixin):
    """ Publisher Workflow State Model. """

    DRAFT = 'draft'
    NEEDS_REVIEW = 'needs_review'
    NEEDS_FINAL_APPROVAL = 'needs_final_approval'
    FINALIZED = 'finalized'
    PUBLISHED = 'published'
    CHOICES = (
        (DRAFT, _('Draft')),
        (NEEDS_REVIEW, _('Needs Review')),
        (NEEDS_FINAL_APPROVAL, _('Needs Final Approval')),
        (FINALIZED, _('Finalized')),
        (PUBLISHED, _('Published'))
    )

    name = FSMField(default=DRAFT, choices=CHOICES)

    history = HistoricalRecords()

    def __str__(self):
        return self.get_name_display()

    @transition(field=name, source='*', target=DRAFT)
    def draft(self):
        # TODO: send email etc.
        pass

    @transition(field=name, source=DRAFT, target=NEEDS_REVIEW)
    def needs_review(self):
        # TODO: send email etc.
        pass

    @transition(field=name, source=NEEDS_REVIEW, target=NEEDS_FINAL_APPROVAL)
    def needs_final_approval(self):
        # TODO: send email etc.
        pass

    @transition(field=name, source=NEEDS_FINAL_APPROVAL, target=FINALIZED)
    def finalized(self):
        # TODO: send email etc.
        pass

    @transition(field=name, source=FINALIZED, target=PUBLISHED)
    def publish(self):
        # TODO: send email etc.
        pass


class Course(TimeStampedModel, ChangedByMixin):
    """ Publisher Course model. It contains fields related to the course intake form."""

    title = models.CharField(max_length=255, default=None, null=True, blank=True, verbose_name=_('Course title'))
    number = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('Course number'))
    short_description = models.CharField(
        max_length=255, default=None, null=True, blank=True, verbose_name=_('Course subtitle')
    )
    full_description = models.TextField(default=None, null=True, blank=True, verbose_name=_('About this course'))
    organizations = models.ManyToManyField(
        Organization, blank=True, related_name='publisher_courses', verbose_name=_('Partner Name')
    )
    level_type = models.ForeignKey(
        LevelType, default=None, null=True, blank=True, related_name='publisher_courses', verbose_name=_('Course level')
    )
    expected_learnings = models.TextField(default=None, null=True, blank=True, verbose_name=_("What you'll learn"))
    syllabus = models.TextField(default=None, null=True, blank=True)
    prerequisites = models.TextField(default=None, null=True, blank=True)
    learner_testimonial = models.CharField(max_length=50, null=True, blank=True)

    primary_subject = models.ForeignKey(
        Subject, default=None, null=True, blank=True, related_name='publisher_courses_primary'
    )
    secondary_subject = models.ForeignKey(
        Subject, default=None, null=True, blank=True, related_name='publisher_courses_secondary'
    )
    tertiary_subject = models.ForeignKey(
        Subject, default=None, null=True, blank=True, related_name='publisher_courses_tertiary'
    )

    history = HistoricalRecords()

    def __str__(self):
        return self.title


class CourseRun(TimeStampedModel, ChangedByMixin):
    """ Publisher CourseRun model. It contains fields related to the course run intake form."""
    PRIORITY_LEVEL_1 = 'L1'
    PRIORITY_LEVEL_2 = 'L2'
    PRIORITY_LEVEL_3 = 'L3'
    PRIORITY_LEVEL_4 = 'L4'
    PRIORITY_LEVEL_5 = 'L5'

    PRIORITY_LEVELS = (
        (PRIORITY_LEVEL_1, _('Level 1')),
        (PRIORITY_LEVEL_2, _('Level 2')),
        (PRIORITY_LEVEL_3, _('Level 3')),
        (PRIORITY_LEVEL_4, _('Level 4')),
        (PRIORITY_LEVEL_5, _('Level 5')),
    )

    state = models.ForeignKey(State, null=True, blank=True)

    course = models.ForeignKey(Course, related_name='publisher_course_runs')
    lms_course_id = models.CharField(max_length=255, unique=True, null=True, blank=True)

    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)
    enrollment_start = models.DateTimeField(null=True, blank=True)
    enrollment_end = models.DateTimeField(null=True, blank=True)
    certificate_generation = models.DateTimeField(null=True, blank=True)
    pacing_type = models.CharField(
        max_length=255, choices=CourseMetadataCourseRun.PACING_CHOICES, db_index=True, null=True, blank=True
    )
    staff = SortedManyToManyField(Person, blank=True, related_name='publisher_course_runs_staffed')
    min_effort = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text=_('Estimated minimum number of hours per week needed to complete a course run.'))
    max_effort = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text=_('Estimated maximum number of hours per week needed to complete a course run.'))
    language = models.ForeignKey(LanguageTag, null=True, blank=True, related_name='publisher_course_runs')
    transcript_languages = models.ManyToManyField(
        LanguageTag, blank=True, related_name='publisher_transcript_course_runs'
    )
    length = models.PositiveIntegerField(
        null=True, blank=True, help_text=_("Length of course, in number of weeks")
    )
    sponsor = models.ManyToManyField(Organization, blank=True, related_name='publisher_course_runs')

    is_re_run = models.BooleanField(default=False)
    is_xseries = models.BooleanField(default=False)
    xseries_name = models.CharField(max_length=255, null=True, blank=True)
    is_micromasters = models.BooleanField(default=False)
    micromasters_name = models.CharField(max_length=255, null=True, blank=True)
    contacted_partner_manager = models.BooleanField(default=False)
    seo_review = models.TextField(
        default=None, null=True, blank=True, help_text=_("SEO review on your course title and short description")
    )
    keywords = models.TextField(
        default=None, blank=True, help_text=_("Please add top 10 comma separated keywords for your course content")
    )
    notes = models.TextField(
        default=None, null=True, blank=True, help_text=_(
            "Please add any additional notes or special instructions for the course About Page."
        )
    )
    target_content = models.BooleanField(default=False)
    priority = models.CharField(
        max_length=5, choices=PRIORITY_LEVELS, null=True, blank=True
    )
    course_team_admins = models.TextField(
        default=None, blank=True, null=True, help_text=_("Comma separated list of edX usernames or emails of admins.")
    )
    course_team_additional_staff = models.TextField(
        default=None, blank=True, null=True, help_text=_(
            "Comma separated list of edX usernames or emails of additional staff."
        )
    )

    history = HistoricalRecords()

    def __str__(self):
        return '{course}: {start_date}'.format(course=self.course.title, start_date=self.start)

    def change_state(self, target=State.DRAFT):
        if target == State.NEEDS_REVIEW:
            self.state.needs_review()
        elif target == State.NEEDS_FINAL_APPROVAL:
            self.state.needs_final_approval()
        elif target == State.FINALIZED:
            self.state.finalized()
        elif target == State.PUBLISHED:
            self.state.publish()
        else:
            self.state.draft()

        self.state.save()

    @property
    def current_state(self):
        return self.state.get_name_display()


class Seat(TimeStampedModel, ChangedByMixin):
    """ Seat model. """
    HONOR = 'honor'
    AUDIT = 'audit'
    VERIFIED = 'verified'
    PROFESSIONAL = 'professional'
    NO_ID_PROFESSIONAL = 'no-id-professional'
    CREDIT = 'credit'

    SEAT_TYPE_CHOICES = (
        (HONOR, _('Honor')),
        (AUDIT, _('Audit')),
        (VERIFIED, _('Verified')),
        (PROFESSIONAL, _('Professional (with ID verification)')),
        (NO_ID_PROFESSIONAL, _('Professional (no ID verifiation)')),
        (CREDIT, _('Credit')),
    )

    PRICE_FIELD_CONFIG = {
        'decimal_places': 2,
        'max_digits': 10,
        'null': False,
        'default': 0.00,
    }
    course_run = models.ForeignKey(CourseRun, related_name='seats')
    type = models.CharField(max_length=63, choices=SEAT_TYPE_CHOICES, verbose_name='Seat type')
    price = models.DecimalField(**PRICE_FIELD_CONFIG)
    currency = models.ForeignKey(Currency, default='USD', related_name='publisher_seats')
    upgrade_deadline = models.DateTimeField(null=True, blank=True)
    credit_provider = models.CharField(max_length=255, null=True, blank=True)
    credit_hours = models.IntegerField(null=True, blank=True)

    history = HistoricalRecords()

    def __str__(self):
        return '{course}: {type}'.format(course=self.course_run.course.title, type=self.type)


@receiver(pre_save, sender=CourseRun)
def initialize_workflow(sender, instance, **kwargs):    # pylint: disable=unused-argument
    """ Create Workflow State For CourseRun Before Saving. """
    create_workflow_state(instance)


def create_workflow_state(course_run):
    """ Create Workflow State If Not Present."""
    if not course_run.state:
        state = State()
        state.save()
        course_run.state = state