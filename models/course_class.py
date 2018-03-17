import re

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError
from datetime import datetime, time, timedelta





# ==========================================================================================================================

class CourseClass(models.Model):
	_name = 'training.center.class'
	_description = 'Opened training classes'

	course_id = fields.Many2one('training.center.course','Course', required=True, ondelete="restrict")
	open_date = fields.Date('Open Date', required=True)
	start_date = fields.Date('Start Date')
	finish_date = fields.Date('Finished Date', readonly=True)
	trainer_id = fields.Many2one('training.center.trainer','Trainer', ondelete="restrict")
	state = fields.Selection((
		('draft','Draft'),
		('open','Open'),
		('ongoing','Ongoing'),
		('done','Done'),
		('canceled','Canceled')
		), 'State', default="draft")
	session_ids = fields.One2many('training.center.class.session','class_id','Sessions')
	participant_ids = fields.One2many('training.center.class.participant','class_id','Participant')
	capacity = fields.Integer('Capacity', required=True)
	open_class = fields.Char(required=True,default='Open Class')
	name = fields.Char('Class Name', size=20, required=True)
	total_sessions = fields.Integer('Total', compute='_compute_total')
	total_participant = fields.Integer('Total Participant', compute='_compute_total')

	_sql_constraints = {
		('check_capacity','CHECK(capacity > 0)','Capacity must be more than zero.'),
		('check_total','CHECK(total_participant > capacity)','Total participant exceed the capacity.'),
	}

	@api.onchange('course_id')
	def onchange_course_id(self):
	# otomatis isi session berdasarkan silabus course
		sessions = []
		for session in self.course_id.syllabus_ids:
			sessions.append([0,False,{
				'sequence': session.sequence,
				'name': session.name,
				'desc': session.desc,
				'duration': session.duration,
				}])
		self.session_ids = sessions
	
		trainer_ids = []
		for trainer in self.course_id.trainer_ids:
			trainer_ids.append(trainer.trainer_id.id)
		domain = [('id','in',trainer_ids)]
		return {
			'domain': {
				'trainer_id': domain,
			}
		}

		participants = []
		for participant in self.participant_ids.participant_id:
			participants.append(participant.participant_id.par_id)
		domain = [('id','in',participants)]
		return {
			'domain': {
				'participant_id': domain,
			}
		}

	@api.constrains('total_participant')
	def _check_total_participant_value(self):
		for record in self:
			if record.total_participant > record.capacity:
				raise ValidationError('Participant has exceed the capacity')

	@api.one
	def open_class(self):
		self.write({
				'state':'open',
				# 'open_date' : fields.Date.context_today(self),
			})
	
	@api.one
	def start_class(self):
		self.write({
			'state':'ongoing',
			'start_date' : fields.Date.context_today(self),
		})

		for session in self.session_ids:
			for participant in self.participant_ids:
				self.env['training.center.class.session.participant.absence'].create({
					'session_id': session.id,
					'class_participant_id': participant.id,
				})
				self.env.cr.commit()

	@api.multi
	def _compute_total(self):
		for record in self:
			record.total_participant = len(record.participant_ids)
			record.total_sessions = len(record.session_ids)
	# 	raise ValidationError(self.total_participant)

# ==========================================================================================================================

class ClassSession(models.Model):
	_name = 'training.center.class.session'
	_description = 'Class sessions'

	class_id = fields.Many2one('training.center.class', 'Class', ondelete="cascade")
	sequence = fields.Integer('Sequence', required=True)
	name = fields.Char('Syllabus Title', size=20, required=True)
	desc = fields.Text('Syllabus Description')
	duration = fields.Float('Syllabus Duration')
	session_start = fields.Datetime('Session Start', required=True)
	session_end = fields.Datetime('Session End', required=True)
	class_participant_absent_ids = fields.One2many('training.center.class.session.participant.absence', 'session_id', 'Participant Absence')

	@api.onchange('duration','session_start')
	def onchange_duration_start(self):
		if not (self.session_start and self.duration): return
		session_start = datetime.strptime(self.session_start, DEFAULT_SERVER_DATETIME_FORMAT)
		session_end = session_start + timedelta(hours=self.duration)	
		self.session_end = session_end.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

# ==========================================================================================================================

class Participant(models.Model):
	_name = 'training.center.participant'
	_description = 'Participant master'

	name = fields.Char('Participant Name' ,size=40, required=True)
	address = fields.Char('Participant Address', size=40, required=True)
	phone = fields.Char('Participant Phone Number', size = 20, required=True)
	email = fields.Char('Participant E-mail', size=50, required=True)
	birth_date = fields.Date('Participant Birth Date', required=True)
	par_id = fields.Char('Participant ID ', size=9, readonly=True)

	_sql_constraints = [
		('unique_email','UNIQUE(email)','Email has already been used.')
	]

	@api.constrains('email')
	def _check_email_value(self):
		email_regex = re.compile(r"[^@]+@[^@]+\.[^@]+")
		for record in self:
			if not email_regex.match(record.email):
				raise ValidationError('E-mail is invalid')

	@api.constrains('phone')
	def _check_phone_value(self):
		for record in self:
			if not record.phone.isdigit():
				raise ValidationError('Invalid Phone Number')

	@api.model
	def create(self, vals):
		#isikan nomor urut peserta secara otomatis
		year = datetime.now().strftime("%Y")
		latest_seq = self.search([('sequence')], order="sequence DESC", limit = 1)
		if len(latest_seq) == 0:
			new_seq = 1
		else:
			latest_seq = latest_seq.sequence
			new_seq = latest_seq.sequence
		vals['sequence'] = new_seq
		return super(Participant, self).create(vals)

	@api.model
	def create(self, vals):
		#isikan nomor urut peserta secara otomatis
		year = datetime.now().strftime("%Y")
		latest_par = self.search([('par_id','like',year)], order="par_id DESC", limit = 1)
		if len(latest_par) == 0:
			new_id = "%s00001" % (year)
		else:
			latest_id = latest_par.par_id
			new_id = str(int(latest_id)+1)
		vals['par_id'] = new_id
		return super(Participant, self).create(vals)
		
	"""
	@api.one
	def _compute_id(self):
		year = datetime.datetime.now().strftime("%Y")
		template = year+"00000"
		par_id = int (template)+self.id
		# self.write('par_id': par_id) 
		self.par_id = par_id
	"""

# ==========================================================================================================================

# buat nampilin participant ke course class
class ClassParticipant(models.Model):
	_name = 'training.center.class.participant'
	_description = 'Class participant'

	class_id = fields.Many2one('training.center.class', 'Class', required=True, ondelete="cascade")
	participant_id = fields.Many2one('training.center.participant','Participant ID', required=True, ondelete="cascade")

	_rec_name = 'participant_id'
	_sql_constraints = {
		('unique_code', 'UNIQUE(class_id,participant_id)', 'Participant have already been registered in this class')
	}

	@api.model
	def create(self, vals):
		# tidak boleh melebihi kapasitas kelas
		class_data = self.env['training.center.class'].browse(vals.get('class_id', None))
		if class_data.total_participant == class_data.capacity:
			raise ValidationError('This class capacity is full.')
		print("%s" % vals)
		return super(ClassParticipant, self).create(vals)

# ==========================================================================================================================

class ParticipantAbsence(models.Model):
	_name = 'training.center.class.session.participant.absence'
	_description = 'Participant absence'

	session_id = fields.Many2one('training.center.class.session', 'Session', ondelete="cascade", required=True)
	class_participant_id = fields.Many2one('training.center.class.participant', 'Class Participant', ondelete="cascade", required=True)
	attendance = fields.Boolean('Attendance', default=False)