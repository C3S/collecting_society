# -*- coding: utf-8 -*-
# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society_docker

Initialize Setup
----------------

Imports::

    >>> import os
    >>> import uuid
    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from proteus import config, Model, Wizard
    >>> today = datetime.date.today()
    >>> now = datetime.datetime.now()
    >>> #import interlude; interlude.interact(locals())

Create database::

    >>> config = config.set_trytond()
    >>> config.pool.test = True

Install collecting_society::

    >>> Module = Model.get('ir.module')
    >>> module, = Module.find(
    ...     [('name', '=', 'collecting_society')])
    >>> Module.activate([module.id], config.context)
    >>> Wizard('ir.module.activate_upgrade').execute('upgrade')

Get some defaults::

    >>> #import interlude; interlude.interact(locals())
    >>> Country = Model.get('country.country')
    >>> Currency = Model.get('currency.currency')
    >>> Language = Model.get('ir.lang')
    >>> germany = Country(name='Germany', code='DE')
    >>> germany.save()
    >>> euro = Currency(name='Euro', code='EUR', symbol='€')
    >>> euro.save()


Setup Collecting Society Company
--------------------------------
Create company::

    >>> Company = Model.get('company.company')
    >>> Party = Model.get('party.party')

    >>> party = Party(
    ...     name='C3S SCE')

    >>> _ = party.addresses.pop()
    >>> party_address = party.addresses.new(
    ...     street='Rochusstraße 44',
    ...     postal_code='40479',
    ...     city='Düsseldorf',
    ...     country=germany)
    >>> party.save()

    >>> company_config = Wizard('company.company.config')
    >>> company_config.execute('company')
    >>> company = company_config.form
    >>> company.party = party
    >>> company.currency = euro
    >>> company_config.execute('add')
    >>> company, = Company.find()

Reload context::

    >>> User = Model.get('res.user')
    >>> config._context = User.get_preferences(True, config.context)

Create payment term::

    >>> PaymentTerm = Model.get('account.invoice.payment_term')
    >>> PaymentTermLine = Model.get('account.invoice.payment_term.line')
    >>> payment_term = PaymentTerm(name='Term')
    >>> payment_term_line = PaymentTermLine(type='remainder', days=14)
    >>> payment_term.lines.append(payment_term_line)
    >>> payment_term.save()

Create fiscal year::

    >>> FiscalYear = Model.get('account.fiscalyear')
    >>> Sequence = Model.get('ir.sequence')
    >>> SequenceStrict = Model.get('ir.sequence.strict')
    >>> fiscalyear = FiscalYear(name='%s' % today.year)
    >>> fiscalyear.start_date = today + relativedelta(month=1, day=1)
    >>> fiscalyear.end_date = today + relativedelta(month=12, day=31)
    >>> fiscalyear.company = company
    >>> post_move_sequence = Sequence(name='%s' % today.year,
    ...     code='account.move', company=company)
    >>> post_move_sequence.save()
    >>> fiscalyear.post_move_sequence = post_move_sequence
    >>> invoice_seq = SequenceStrict(name=str(today.year),
    ...     code='account.invoice', company=company)
    >>> invoice_seq.save()
    >>> fiscalyear.out_invoice_sequence = invoice_seq
    >>> fiscalyear.in_invoice_sequence = invoice_seq
    >>> fiscalyear.out_credit_note_sequence = invoice_seq
    >>> fiscalyear.in_credit_note_sequence = invoice_seq
    >>> fiscalyear.save()
    >>> FiscalYear.create_period([fiscalyear.id], config.context)

Create chart of accounts::

    >>> AccountTemplate = Model.get('account.account.template')
    >>> Account = Model.get('account.account')
    >>> account_template, = AccountTemplate.find([('parent', '=', None)])
    >>> create_chart = Wizard('account.create_chart')
    >>> create_chart.execute('account')
    >>> create_chart.form.account_template = account_template
    >>> create_chart.form.company = company
    >>> create_chart.execute('create_account')
    >>> receivable, = Account.find([
    ...         ('kind', '=', 'receivable'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> payable, = Account.find([
    ...         ('kind', '=', 'payable'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> revenue, = Account.find([
    ...         ('kind', '=', 'revenue'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> expense, = Account.find([
    ...         ('kind', '=', 'expense'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> cash, = Account.find([
    ...         ('kind', '=', 'other'),
    ...         ('company', '=', company.id),
    ...         ('name', '=', 'Main Cash'),
    ...         ])
    >>> account_tax, = Account.find([
    ...         ('kind', '=', 'other'),
    ...         ('company', '=', company.id),
    ...         ('name', '=', 'Main Tax'),
    ...         ])

    >>> create_chart.form.account_receivable = receivable
    >>> create_chart.form.account_payable = payable
    >>> create_chart.execute('create_properties')


Create tax::

    >>> TaxCode = Model.get('account.tax.code')
    >>> Tax = Model.get('account.tax')
    >>> tax = Tax()
    >>> tax.name = '19% Mehrwertsteuer'
    >>> tax.description = '19% Mehrwertsteuer'
    >>> tax.type = 'percentage'
    >>> tax.rate = Decimal('.19')
    >>> tax.invoice_account = account_tax
    >>> tax.credit_note_account = account_tax
    >>> invoice_base_code = TaxCode(name='invoice base')
    >>> invoice_base_code.save()
    >>> tax.invoice_base_code = invoice_base_code
    >>> invoice_tax_code = TaxCode(name='invoice tax')
    >>> invoice_tax_code.save()
    >>> tax.invoice_tax_code = invoice_tax_code
    >>> credit_note_base_code = TaxCode(name='credit note base')
    >>> credit_note_base_code.save()
    >>> tax.credit_note_base_code = credit_note_base_code
    >>> credit_note_tax_code = TaxCode(name='credit note tax')
    >>> credit_note_tax_code.save()
    >>> tax.credit_note_tax_code = credit_note_tax_code
    >>> tax.save()

Create Transitory account::

    >>> AccountType = Model.get('account.account.type')
    >>> root_account_type, = AccountType.find([
    ...     ('name', '=', 'Minimal Account Type Chart')])
    >>> transit_account_type = AccountType(
    ...     name='Transit',
    ...     parent=root_account_type,
    ...     balance_sheet=True,
    ...     company=company)
    >>> transit_account_type.save()
    >>> root_account, = Account.find([('name', '=', 'Minimal Account Chart')])
    >>> transit_account = Account(
    ...     name='Main Transit',
    ...     type=transit_account_type,
    ...     kind='other',
    ...     parent=root_account,
    ...     company=company)
    >>> transit_account.save()
    >>> AccountJournal = Model.get('account.journal')
    >>> sequence_journal, = Sequence.find([('code', '=', 'account.journal')])
    >>> journal = AccountJournal(
    ...     name='Transit', code='TRANS', type='general',
    ...     sequence=sequence_journal)
    >>> journal.save()
    >>> #import interlude; interlude.interact(locals())

Create separate escrow bank account and journal for colleting money which is
not owned by C3S::

    >>> current_account_type = AccountType.find(
    ...     [('name', '=', 'Cash')])[0].parent
    >>> escrow_account_type = AccountType(
    ...     name='Escrow',
    ...     parent=current_account_type,
    ...     company=company)
    >>> escrow_account_type.save()
    >>> escrow_account = Account(
    ...     name='Main Escrow',
    ...     type=current_account_type,
    ...     kind='other',
    ...     deferral=True,
    ...     parent=root_account,
    ...     company=company)
    >>> escrow_account.save()
    >>> escrow_journal = AccountJournal(
    ...     name='Escrow',
    ...     code='ESCR',
    ...     type='cash',
    ...     debit_account=escrow_account,
    ...     credit_account=escrow_account,
    ...     sequence=sequence_journal)
    >>> escrow_journal.save()



Web-User Scenario
=================

The web user scenario tests the authentication functionalities for a new user
to become a valid web user.

Create a web user::

    >>> WebUser = Model.get('web.user')
    >>> web_user = WebUser()

Set login credentials and other essentials::

    >>> web_user.email = 'wilbert_webuser@c3s.cc'
    >>> web_user.password = 'wu'
    >>> web_user.nickname = 'wil'
    >>> web_user.save()

Check opt-in state::

    >>> assert(web_user.opt_in_state == 'new')

Check opt-in link is a correctly formatted UUID::

    >>> assert(bool(uuid.UUID(web_user.opt_in_uuid, version=4)))

Double opt-in Email with UUID in link is send by the portal::

    >>> web_user.opt_in_state = 'mail-sent'
    >>> web_user.save()

The web user clicks on the link sent by the portal.
The received UUID is equal to the stored UUID in web_user.opt_in_uuid::

    >>> web_user.opt_in_state = 'opted-in'
    >>> web_user.save()

Now the web user is a valid portal user.

If the web user tries to login with wrong credentials
(email: wilbert_webuser@c3s.cc and password: wuXXX) the
authentication result is None::

    >>> logged_in_web_user = WebUser.authenticate(
    ...     'wilbert_webuser@c3s.cc','wuXXX',config.context)
    >>> assert(type(logged_in_web_user) == type(None))


If the web user tries to login with his credentials
(email: wilbert_webuser@c3s.cc and password: wu) the authentication
result is the authenticated web user object::

    >>> logged_in_web_user = WebUser.authenticate(
    ...     'wilbert_webuser@c3s.cc',
    ...     'wu',
    ...     config.context)
    >>> assert(logged_in_web_user)
    >>> logged_in_web_user
    Pool().get('web.user')(1)

    >>> logged_in_web_user = WebUser(logged_in_web_user.id)
    >>> assert(logged_in_web_user.nickname == u'wil')


Licenser Scenario
=================

A valid licenser web user. See Web-User Scenario for details::

    >>> licenser = WebUser()
    >>> licenser.email='cres_licenser@c3s.cc'
    >>> licenser.password='cc'
    >>> web_user.nickname = 'wil'
    >>> licenser.opt_in_state = 'opted-in'
    >>> licenser.save()

Add another person name::

    >>> licenser.party.name = 'Crescentia Creative'

Define roles::

    >>> WebUserRole = Model.get('web.user.role')
    >>> licenser.default_role = 'licenser'
    >>> licenser.roles.extend(
    ...     WebUserRole.find([('name', '=', 'licenser')]))

Add an address::

    >>> Address = Model.get('party.address')
    >>> licenser.party.addresses.append(
    ...     Address(
    ...         street='Berliner Strasse 123',
    ...         postal_code='51063',
    ...         city='Köln',
    ...         country=germany))

Save licenser web user::

    >>> licenser.save()

Add a bank account for the licenser::

    >>> Bank = Model.get('bank')
    >>> BankAccount = Model.get('bank.account')
    >>> BankAccountNumber = Model.get('bank.account.number')
    >>> licenser_bank_account = BankAccount(currency=euro)
    >>> licenser_bank_account.bank = Bank(
    ...     bic='AACSDE33', party=Party(name='Sparkasse Aachen'))
    >>> licenser_bank_account.owners.append(licenser.party)
    >>> licenser_bank_account.numbers.append(
    ...     BankAccountNumber(
    ...         type='iban', number='DE70 3905 0000 0012 3456 78'))
    >>> licenser_bank_account.bank.party.save()
    >>> licenser_bank_account.bank.save()
    >>> licenser_bank_account.save()


Artist Scenario
===============

Add band /'angstalt/ and solo artist members::

    >>> Artist = Model.get('artist')
    >>> angstalt = Artist(
    ...     name="/'ʌŋʃtʌlt/",
    ...     group=True,
    ...     description='''
    ...     /'angstalt/ was founded in 1995 by the twin brothers Stefan
    ...     Hintz (bass, keyboards) and Norman Hintz (drums, percussion)
    ...     as well as Meik "m." Michalke (guitar, voice, bass).
    ...     In the early phase, which was marked by the self-released debut
    ...     "ex." (1998) and the retrospective archive sampler
    ...     "[ha1b:2ehn]" (2000), the project would be completed by Alex
    ...     Pavlidis (bass, voice), until he became full-time bassist with
    ...     Sometree in 2002.
    ...
    ...     Since 2005 until now /'angstalt/ consists of Stefan Hintz (bass,
    ...     keyboards), Norman Hintz (drums, percussion) Tobias "Rettich"
    ...     Rettstadt (drums, bass, keyboards) and Meik "m." Michalke (
    ...     guitar, voice, bass). Yes, that's two drummers.
    ...
    ...     m. released two books of poems as of yet, "zur blütezeit in
    ...     herzwüsten (ein floristisches handbuch zur steingärtnerei)" and
    ...     "phantomherzen". Since 2005 he's also responsible (under his
    ...     legal name) for a germany-wide Creative Commons project called
    ...     OpenMusicContest.org.
    ...
    ...     Concerts are quite rare (e.g., 2008 as support for Cranes).
    ...     If you don't want to miss one of the intense appearances, you
    ...     should subscribe to the newsletter.
    ...
    ...     Source Text: https://www.jamendo.com/de/artist/364964/angstalt
    ...     Source Picture: http://www.angstalt.de/bilder/logo_dbz_degb.png
    ...     Date of last access: 2015-04-09 18:00''',
    ...     entity_creator=web_user
    ... )
    >>> member = angstalt.solo_artists.new(
    ...     name='Stefan Hintz',
    ...     entity_creator=web_user
    ... )
    >>> member = angstalt.solo_artists.new(
    ...     name='Norman Hintz',
    ...     entity_creator=web_user
    ... )
    >>> member = angstalt.solo_artists.new(
    ...     name='m.',
    ...     entity_creator=web_user
    ... )
    >>> member = angstalt.solo_artists.new(
    ...     name='Tobias "Rettich" Rettstadt',
    ...     entity_creator=web_user
    ... )
    >>> angstalt.save()

Check if artist has no access parties::

    >>> angstalt.access_parties
    []

Artist Claim
------------
A newly created web user named 'meik' ...::

    >>> meik = WebUser()
    >>> meik.email = 'meik@c3s.cc'
    >>> meik.password = 'meik'
    >>> meik.nickname = 'm.'
    >>> meik.opt_in_state = 'opted-in'
    >>> meik.save()
    >>> meik.party.name = 'Meik Michalke'
    >>> meik.party.save()

... wanted to claim the solo artist "m."::

    >>> solo_artist, = Artist.find([('name', '=', 'm.')])

.. note:: The process of validating the artist claim is done separately.

In case the claim is successfully validated, the solo artist
"m." is manually append to the artists of webuser meik as an
administrative task::

    >>> solo_artist.party = meik.party
    >>> solo_artist.save()

Web user meik can become payee of the solo artist::

    >>> solo_artist.payee = meik.party
    >>> solo_artist.save()

Web user meik has a bank account::

    >>> meik_bank_account = BankAccount(currency=euro)
    >>> meik_bank_account.bank, = Bank.find([('bic', '=', 'AACSDE33')])
    >>> meik_bank_account.owners.append(meik.party)
    >>> meik_bank_account.numbers.append(
    ...     BankAccountNumber(
    ...         type='iban', number='DE53 1203 0000 0011 1111 11'))
    >>> meik_bank_account.bank.party.save()
    >>> meik_bank_account.bank.save()
    >>> meik_bank_account.save()
    >>> meik.reload()

Web user meik also wants to become payee of the group angstalt, because he is
a band member::

    >>> angstalt.payee = meik.party
    >>> angstalt.save()

.. note:: The process of validating an artist payee is done separately.


Webuser meik, the only member of the group angstalt can be administrative
validated as payee::

    >>> angstalt.valid_payee = True


Webuser Invitation
------------------

Web user meik from the band /'angstalt/ wants to invite more members of his
band.
He invites his colleague Tobias to claim the artist
Tobias "Rettich" Rettstadt.
The artist of his colleage has the unique identifier::

    >>> artist_to_invite, = Artist.find(
    ...     [('name', '=', 'Tobias "Rettich" Rettstadt')])
    >>> token = artist_to_invite.invitation_token

.. note:: The system sends an email to the email address of the
    web user to invite (tobias), given by the inviting web user (meik).

The email recipient sends us the token back and needs to authenticate
as a web user.
In this case the web user does not exist and is created as the new web user
tobi::

    >>> tobi = WebUser()
    >>> tobi.email = 'tobi@c3s.cc'
    >>> tobi.password = 'tobi'
    >>> tobi.nickname = 'Rettich'
    >>> tobi.opt_in_state = 'opted-in'
    >>> tobi.save()
    >>> tobi.party.name = 'Tobias Rettstadt'

In the invitation email from tobis colleague meik is a reference token for
an artist::

    >>> solo_artist, = Artist.find([('invitation_token', '=', token)])

The identified solo artist will be added to the web user tobi.

.. note:: The process of validating the artist claim is done separately.

In case the claim is successfully validated, the solo artist
'Tobias "Rettich" Rettstadt' is append to the artists of
web user tobi in an administrative task::

    >>> solo_artist.party = tobi.party
    >>> solo_artist.save()

Check the count of access parties to Band angstalt::

    >>> len(angstalt.access_parties)
    2

The parties of web user meik and tobi have access to angstalt::

    >>> angstalt.access_parties == [tobi.party, meik.party]
    True


Payee Proposal
--------------
Web user tobi wanted to become a new payee for the band angstalt.
The actual payee of angstalt is meik and there is no actual proposal
for a new payees::

    >>> angstalt.payee == meik.party
    True
    >>> angstalt.valid_payee
    True
    >>> angstalt.payee_proposal is None
    True

Tobi proposes himself as a new payee::

    >>> angstalt.payee_proposal = tobi.party
    >>> angstalt.save()

When adding a new proposal, the status of the actual payee is
automatically set to invalid::

    >>> bool(angstalt.valid_payee)
    False

The valid payee flag is used to control payments to the actual payee.
If the payee is invalid, no money is paid to any bank account.

Now the members of the band can vote (accept) for the proposed payee by adding
themselves to the list of payee acceptances::

    >>> angstalt.payee_acceptances.append(meik.party)
    >>> angstalt.payee_acceptances == angstalt.access_parties
    False

The proposed payee is accepted, when every web user party in the
access parties list accepts the new payee::

    >>> angstalt.payee_acceptances.append(tobi.party)
    >>> sorted(angstalt.payee_acceptances) == sorted(angstalt.access_parties)
    True

In case everyone accepts the new payee, the payee field is updated::

    >>> angstalt.payee = angstalt.payee_proposal
    >>> angstalt.save()
    >>> angstalt.reload()

The clean up for the next vote is partially done automatically::

    >>> angstalt.payee_proposal is None
    True
    >>> bool(angstalt.valid_payee)
    False
    >>> for i in range(len(angstalt.payee_acceptances)):
    ...     _ = angstalt.payee_acceptances.pop()
    >>> angstalt.save()

Bank Accounts
-------------
The band has an own bank account.
For this, the band is a legal entity having an own party::

    >>> angstalt.party = Party(name="/'angstalt/")
    >>> angstalt.party.save()
    >>> angstalt.save()

Add bank account to the band::

    >>> angstalt_bank_account = BankAccount(currency=euro)
    >>> angstalt_bank_account.bank, = Bank.find([('bic', '=', 'AACSDE33')])
    >>> angstalt_bank_account.owners.append(angstalt.party)
    >>> angstalt_bank_account.numbers.append(
    ...     BankAccountNumber(
    ...         type='iban', number='DE59 3905 0000 0022 2222 22'))
    >>> angstalt_bank_account.bank.party.save()
    >>> angstalt_bank_account.bank.save()
    >>> angstalt_bank_account.save()
    >>> angstalt.reload()


Repertoire Scenario
===================

Repertoire upload
-----------------

Create a web user for this scenario::

    >>> web_user = WebUser()

Set login credentials and other essentials and opt-in::

    >>> web_user.email = 'max_repertoire@c3s.cc'
    >>> web_user.password = 'mr'
    >>> web_user.nickname = 'maxr'
    >>> web_user.opt_in_state = 'opted-in'
    >>> web_user.save()

Get required objects and login user::

    >>> Content = Model.get('content')
    >>> content = Content()
    >>> web_user_max = WebUser.authenticate(
    ... 'max_repertoire@c3s.cc','mr',config.context)
    >>> web_user_max = WebUser(web_user_max.id)

Create valid content::

    >>> content.active = True
    >>> content.uuid = 'a3d55e8e-18c3-4a22-a11b-ec5dc4a1ce29'
    >>> content.preview_path = '/shared/tmp/upload/previews/a/3/a3d55e8e-18c3-4a22-a11b-ec5dc4a1ce29'
    >>> content.sample_rate = 48000
    >>> content.pre_ingest_excerpt_score = 0
    >>> content.channels = 2
    >>> content.name = 'scenario_test_content_dropped.wav'
    >>> content.entity_origin = 'direct'
    >>> content.entity_creator = web_user_max.party
    >>> content.size = 321542
    >>> content.category = 'audio'
    >>> content.post_ingest_excerpt_score = 0
    >>> content.processing_hostname = '4f7dd1c466d6'
    >>> content.lenght = 1
    >>> content.sample_width = 16
    >>> content.mime_type = 'audio/x-wav'
    >>> content.processing_state = 'dropped'
    >>> content.write_date = datetime.datetime.now()
    >>> content.commit_state = 'uncommited'
    >>> content.save()

Create format error content::

    >>> content = Content()
    >>> content.active = True
    >>> content.uuid = 'a3d55e8e-18c3-4a22-a11b-ec5dc4a1ce30'
    >>> content.preview_path = '/shared/tmp/upload/previews/a/3/a3d55e8e-18c3-4a22-a11b-ec5dc4a1ce30'
    >>> content.sample_rate = 48000
    >>> content.pre_ingest_excerpt_score = 0
    >>> content.channels = 2
    >>> content.name = 'scenario_test_wrong_format.pdf'
    >>> content.entity_origin = 'direct'
    >>> content.entity_creator = web_user_max.party
    >>> content.size = 320000
    >>> content.category = 'audio'
    >>> content.post_ingest_excerpt_score = 0
    >>> content.processing_hostname = '4f7dd1c466d6'
    >>> content.lenght = 1
    >>> content.sample_width = 16
    >>> content.mime_type = 'application/pdf'
    >>> content.processing_state = 'rejected'
    >>> content.rejection_reason = 'format_error'
    >>> content.write_date = datetime.datetime.now()
    >>> content.commit_state = 'uncommited'
    >>> content.save()

Create lossy compression content::

    >>> content = Content()
    >>> content.active = True
    >>> content.uuid = 'a3d55e8e-18c3-4a22-a11b-ec5dc4a1ce31'
    >>> content.preview_path = '/shared/tmp/upload/previews/a/3/a3d55e8e-18c3-4a22-a11b-ec5dc4a1ce31'
    >>> content.sample_rate = 48000
    >>> content.pre_ingest_excerpt_score = 0
    >>> content.channels = 2
    >>> content.name = 'scenario_test_lossy_compression.mp3'
    >>> content.entity_origin = 'direct'
    >>> content.entity_creator = web_user_max.party
    >>> content.size = 320000
    >>> content.category = 'audio'
    >>> content.post_ingest_excerpt_score = 0
    >>> content.processing_hostname = '4f7dd1c466d6'
    >>> content.lenght = 1
    >>> content.sample_width = 16
    >>> content.mime_type = 'audio/x-mpeg'
    >>> content.processing_state = 'rejected'
    >>> content.rejection_reason = 'lossy_compression'
    >>> content.write_date = datetime.datetime.now()
    >>> content.commit_state = 'uncommited'
    >>> content.save()
