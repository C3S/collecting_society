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
    >>> from trytond.tests.tools import activate_modules
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.account.tests.tools import create_fiscalyear, \
    ...     create_chart, get_accounts, create_tax, create_tax_code
    >>> from trytond.modules.account_invoice.tests.tools import \
    ...     set_fiscalyear_invoice_sequences

    >>> today = datetime.date.today()
    >>> now = datetime.datetime.now()
    >>> #import interlude; interlude.interact(locals())

Activate modules::

    >>> config = activate_modules('collecting_society')

Get some defaults::

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

    >>> Party = Model.get('party.party')
    >>> party = Party(name='C3S SCE')
    >>> _ = party.addresses.pop()
    >>> party_address = party.addresses.new(
    ...     street='Rochusstraße 44',
    ...     postal_code='40479',
    ...     city='Düsseldorf',
    ...     country=germany)
    >>> tax_identifier = party.identifiers.new()
    >>> tax_identifier.type = 'eu_vat'
    >>> tax_identifier.code = 'BE0897290877'
    >>> _ = create_company(party=party, currency=euro)
    >>> company = get_company()

Create fiscal year::

    >>> fiscalyear = set_fiscalyear_invoice_sequences(
    ...     create_fiscalyear(company))
    >>> fiscalyear.click('create_period')
    >>> period = fiscalyear.periods[0]
    >>> period_ids = [p.id for p in fiscalyear.periods]

Create chart of accounts::

    >>> _ = create_chart(company)
    >>> accounts = get_accounts(company)
    >>> receivable = accounts['receivable']
    >>> revenue = accounts['revenue']
    >>> expense = accounts['expense']
    >>> account_tax = accounts['tax']
    >>> account_cash = accounts['cash']

Create tax::

    >>> TaxCode = Model.get('account.tax.code')
    >>> tax = create_tax(Decimal('.19'))
    >>> tax.save()
    >>> invoice_base_code = create_tax_code(tax, 'base', 'invoice')
    >>> invoice_base_code.save()
    >>> invoice_tax_code = create_tax_code(tax, 'tax', 'invoice')
    >>> invoice_tax_code.save()
    >>> credit_note_base_code = create_tax_code(tax, 'base', 'credit')
    >>> credit_note_base_code.save()
    >>> credit_note_tax_code = create_tax_code(tax, 'tax', 'credit')
    >>> credit_note_tax_code.save()

Create payment term::

    >>> PaymentTerm = Model.get('account.invoice.payment_term')
    >>> payment_term = PaymentTerm(name='Term')
    >>> line = payment_term.lines.new(type='percent', ratio=Decimal('.5'))
    >>> delta, = line.relativedeltas
    >>> delta.days = 20
    >>> line = payment_term.lines.new(type='remainder')
    >>> delta = line.relativedeltas.new(days=40)
    >>> payment_term.save()

Create Transitory account::

    >>> AccountType = Model.get('account.account.type')
    >>> root_account_type, = AccountType.find([
    ...     ('name', '=', 'Minimal Account Type Chart')])
    >>> transit_account_type = AccountType(
    ...     name='Transit',
    ...     parent=root_account_type,
    ...     statement='balance',
    ...     company=company)
    >>> transit_account_type.save()
    >>> Account = Model.get('account.account')
    >>> root_account, = Account.find([('name', '=', 'Minimal Account Chart')])
    >>> transit_account = Account(
    ...     name='Main Transit',
    ...     type=transit_account_type,
    ...     parent=root_account,
    ...     company=company)
    >>> transit_account.save()
    >>> Sequence = Model.get('ir.sequence')
    >>> sequence_journal, = Sequence.find([('name', '=', 'Default Account Journal')])
    >>> AccountJournal = Model.get('account.journal')
    >>> journal = AccountJournal(
    ...     name='Transit', code='TRANS', type='general',
    ...     sequence=sequence_journal)
    >>> journal.save()

Create separate escrow bank account and journal for colleting money which is
not owned by C3S::

    >>> current_account_type = AccountType.find(
    ...     [('name', '=', 'Cash')])[0].parent
    >>> escrow_account_type = AccountType(
    ...     name='Escrow',
    ...     parent=current_account_type,
    ...     statement=current_account_type.statement,
    ...     company=company)
    >>> escrow_account_type.save()
    >>> escrow_account = Account(
    ...     name='Main Escrow',
    ...     type=current_account_type,
    ...     deferral=True,
    ...     parent=root_account,
    ...     company=company)
    >>> escrow_account.save()
    >>> escrow_journal = AccountJournal(
    ...     name='Escrow',
    ...     code='ESCR',
    ...     type='cash',
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
    >>> web_user.password = 'password123'
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
    ...     'password123',
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
    >>> licenser.password='password123'
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
    >>> meik.password = 'password123'
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
    >>> tobi.password = 'password123'
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
    >>> set(angstalt.payee_acceptances) == set(angstalt.access_parties)
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
    >>> web_user.password = 'password123'
    >>> web_user.nickname = 'maxr'
    >>> web_user.opt_in_state = 'opted-in'
    >>> web_user.save()

Get required objects and login user::

    >>> Content = Model.get('content')
    >>> content = Content()
    >>> web_user_max = WebUser.authenticate(
    ... 'max_repertoire@c3s.cc','password123',config.context)
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
    >>> content.length = 1
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
    >>> content.length = 1
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
    >>> content.length = 1
    >>> content.sample_width = 16
    >>> content.mime_type = 'audio/x-mpeg'
    >>> content.processing_state = 'rejected'
    >>> content.rejection_reason = 'lossy_compression'
    >>> content.write_date = datetime.datetime.now()
    >>> content.commit_state = 'uncommited'
    >>> content.save()
