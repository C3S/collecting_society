Collection
==========

Live
----

.. uml::

    skinparam ParticipantBackgroundColor Green
    skinparam ParticipantFontColor White
    skinparam NoteBackgroundColor White
    skinparam NoteBackgroundColor<<State>> LightSteelBlue

    ' -------------------------------------------------------------------------

    actor JobOrStaff as staff
    actor Licensee as licensee

    ' Declaration -------------------------------------------------------------

    rnote over licensee
    declares
    utilisation
    end rnote

    create participant Declaration as declaration
    licensee --> declaration : new

    hnote over declaration <<State>> : created

    create participant Utilisation as utilisation
    declaration --> utilisation : new

    rnote over utilisation
    calculates
    estimated
    amounts
    end rnote

    hnote over utilisation <<State>> : estimated

    ' Confirmation ------------------------------------------------------------

    licensee -> utilisation: confirms Utilisation

    rnote over utilisation
    calculates
    confirmed
    amounts
    end rnote

    hnote over utilisation <<State>> : confirmed

    ' Playlists ---------------------------------------------------------------

    licensee -> utilisation: provides Playlists

    rnote over utilisation
    calculates
    represented
    ratio
    end rnote

    rnote over utilisation
    calculates
    confirmed
    amounts
    end rnote

    staff -> utilisation: finalizes Utilisation

    rnote over utilisation
    adds missing
    playlist fee
    end rnote

    rnote over utilisation
    calculates
    confirmed
    amounts
    end rnote

    hnote over utilisation <<State>> : finalized

    ' Collection --------------------------------------------------------------

    create participant Collection as collection
    staff -> collection : runs a collection

    collection --> utilisation : allocates

    ' Allocation --------------------------------------------------------------

    create participant Allocation as allocation
    utilisation --> allocation : new
    hnote over allocation <<State>> : created
    allocation --> utilisation
    hnote over utilisation <<State>> : allocated

    collection --> allocation : calculates amounts
    hnote over allocation <<State>> : calculated

    ' Invoice -----------------------------------------------------------------

    collection --> allocation : creates invoices
    create participant Invoice as invoice
    allocation --> invoice : new
    hnote over invoice <<State>> : draft
    invoice --> allocation
    hnote over allocation <<State>> : invoiced

    staff -> invoice : validates invoice
    hnote over invoice <<State>> : validated

    staff -> invoice : posts invoice
    invoice --> allocation
    rnote over allocation
    creates
    MoveLines
    end rnote
    allocation --> invoice
    hnote over invoice <<State>> : posted

    staff -> invoice : checks invoice payment status
    invoice --> allocation
    rnote over allocation
    creates
    MoveLines
    end rnote
    hnote over allocation <<State>> : collected
    allocation --> invoice
    hnote over invoice <<State>> : paid

