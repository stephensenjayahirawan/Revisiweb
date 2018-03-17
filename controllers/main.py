import re

from odoo import http
from odoo.exceptions import ValidationError



# ==========================================================================================================================

class Academy(http.Controller):
	
	@http.route('/classes', auth='public', type='http', website=True)
	def index(self, **kwargs):
		mode = http.request.env['training.center.class']
		classes = mode.search([['state', '=', 'open']])
		return http.request.render('training_center.index', {
			'classes': classes
		})

	@http.route('/classes/register/<int:id>', auth='public', type='http', website=True)
	def form(self, id):
		mode = http.request.env['training.center.class']
		classes = mode.search([['state', '=', 'open']])
		return http.request.render('training_center.form', {
			'classes': classes, 'id': id
		})

	@http.route('/classes/register', auth='public', type='http', website=True)
	def form_empty(self):
		mode = http.request.env['training.center.class']
		classes = mode.search([['state', '=', 'open']])
		return http.request.render('training_center.form', {
			'classes': classes, 'id': -1
		})

	@http.route('/classes/save_registration', auth='public', type='http', website=True)
	def insert(self, **kwargs):
		part = http.request.env['training.center.participant']
		participant = part.search([['email', '=', kwargs['email']]])
		ob = {}
		ob['class_id'] = int(kwargs['course_class_id'])
		ob['participant_id'] = participant.id
		if len(participant)==0:
			obj = {}
			obj['name'] = kwargs['name']
			obj['email'] = kwargs['email']
			obj['address'] = kwargs['address']
			obj['phone'] = kwargs['phone']
			obj['birth_date'] = kwargs['birth_date']
			x = part.create(obj)
			ob['participant_id'] = x.id
			cp = http.request.env['training.center.class.participant']
			cp.create(ob)
		else:
			participant.write({
				'name': kwargs['name'],
				'address': kwargs['address'],
				'phone': kwargs['phone'],
				'birth_date': kwargs['birth_date'],
				})
		mode = http.request.env['training.center.class']
		classes = mode.search([['state', '=', 'open']])
		return http.request.render('training_center.index', {
			'classes': classes
		})
