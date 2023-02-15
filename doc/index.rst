Invoicing
=========

Basic Accounting Setup
----------------------
0. Install Module account_de_skr03::

   $ git clone https://github.com/tryton/account_de_skr03 -b 3.4
   $ pip install -e account_de_skr03
   $ trytond -d c3s -c /path/to/trytond.conf -u account_de_skr03

1. Add new Party / Configuration / Company: Name: C3S, Currency: EUR
2. Add a new Employee to the Company
3. Add Company and Employee to Administration /Users /Users to the loggesd-in
   user
4. Financial / Configuration / General Accounts / Create Chart of Accounts, use
   "Kontenplan SKR03 (Germany)" as template and set default accounts (takes
   several minutes, be patient).
5. Create Financial / Configuration / Payment Term: Type: Remainder,
   Number of Days: 14
6. The allocation party needs to set up a customer payment term and an
   account receivable
7. Create products to manage administration and distribution amounts and select
   them in the tarif categories. Set the products as follows:

   * Type to Service,
   * Default UOM to Unit,
   * Account Revenue to 8400 Erlöse 19%,
   * List price to the default fee/amount,
   * Cost price to 0
   * Customer Taxes to 19%

8. To post invocies it is needed create a Financial / Configuration / Fiscal
   Years. Create Fiscalyear for the current year with settings:

   * name: YYYY the year number
   * Starting date: YYYY-01-01
   * Ending date: YYYY-12-31
   * Sequences: Create one sequence for Post Move Sequence and at least one
     other for the invoices/credit note
   * create monthly or quartrly periods.

Allocation Invoicing Workflow
-----------------------------
1. Choose one or more allocations
2. Select Action / Invoice

   * Invoice party is copied from the allocation party
   * For each utilisation of the allocation an invoice line is created

     * Only utilisations in state "Confirmed" are processed.

   * An invoice is created when it has at least one invoice line.

Allocation model provides a relate to show all related invoices.
