```markdown
# Infection Surveillance Module Rules

Enter residents with signs and/or symptoms of infections, under additional precautions, where treatment is being provided, etc.
Not to be used for tracking residents/staff on isolation that are asymptomatic and/or negative for an organism.

## Entering a New Case

| Case Details Field | Filter Selection/Definition | Notes |
|--------------------|-----------------------------|-------|
| Individual Type    | Select Staff or Resident     |       |
| Unit               | Select as appropriate (*will auto populate if Individual is selected first) | |
| Individual:        | Select as appropriate        |       |
| Infection Site     | Select as appropriate from drop down and following case definitions | Click on the !info icon in the upper right corner for definitions |
|                    | **Note do not use the following** |       |
|                    | - Hep B/Hep C – enter as BSI |       |
|                    | - Prostatitis – skin - soft tissue |       |
|                    | - Yeast infections - skin - fungal |       |
|                    | - Parotitis – Skin – soft tissue |       |
|                    | - Tooth/gum – skin and soft tissue |       |
|                    | - Diverticulitis - skin - soft tissue if an actual infection, do not enter if inflammation/flare-up |       |
|                    | - Osteomyelitis – choose SKIN if began with wound infection, if not choose OTHER |       |
| Type               | Select as per case definitions | Click on the !info icon in the upper right corner for definitions |
| Symptoms           | Select as appropriate        |       |
| Onset Date         | Date of symptom onset positive specimen collected, whichever is sooner |       |
| Origin             | HAI – acquired in the home   |       |
|                    | Community Acquired – acquired outside the home |       |
|                    | Other – do not use          |       |
|                    | NOT SELECTED - if unknown   |       |
| Confirmed          | Confirm infections for any of the following | Once confirmed, STATUS icon appears RED |
|                    | - meets case definition found under |       |
|                    | - listed on provincial reportable disease/disease of public health significance list | See Provincial regulations for list of reportable diseases |
|                    | - ARO is identified         |       |
|                    | - meets outbreak case definition |       |

**Effective Date:** July 19, 2024
```

# Updating an Infection

Select resident name in table

## Case Details

| Field              | Filter Selection/Definition                    | Notes                                                                 |
|--------------------|------------------------------------------------|-----------------------------------------------------------------------|
| Name               | Populated                                      |                                                                       |
| Infection Site     | Populated                                      | Infection Site can be updated, but symptoms will need to be reentered |
| Type               | Populated                                      | Can be adjusted as appropriate                                         |
| Origin             | Populated                                      | Can be adjusted as appropriate                                         |
| Onset Date         | Populated                                      | Can be adjusted as appropriate                                         |
| Symptoms           | Populated                                      | Add new symptoms under Signs and Symptoms tab                         |
| Confirmed          | Confirm infections for any of the following    | Once confirmed, STATUS icon appears RED                               |
|                    | • meets case definition found under            |                                                                       |
|                    | • listed on provincial reportable              | See Provincial regulations for list of reportable diseases           |
|                    |   disease/disease of public health             |                                                                       |
|                    |   significance list                            |                                                                       |
|                    | • ARO is identified                            |                                                                       |
|                    | • meets outbreak case definition               |                                                                       |
| Primary            | Populates once Lab Result has been updated     | Leave blank until organism is isolated with results                   |
| Organism           |                                                |                                                                       |
| Treatment          | Do not use                                     |                                                                       |
| Precaution         | Select as appropriate                          | Must be manually added and ended for each infection/colonization      |
| Notification       | Not required field; may select as appropriate   |                                                                       |
| Contact            | Not required field; select as appropriate       |                                                                       |
| Resolution Date    | Day infection resolved and/or treatment finished|                                                                       |
| Outcome            | CHRONIC – use for chronic Hep B/ Hep C/HIV;   | do not use for other infections                                       |
|                    | DECEASED – if infection is cause of death or   | contributing factor, regardless of resolved date                      |
|                    | DISCHARGED – if resident is discharged from     | home or death is not contributed to the infection                     |
|                    | HOSPITALIZED – when resident is sent to        | hospital. Change back if resident returns to home with infection still active |
|                    | RESOLVED - when infection is no longer active/has been resolved |                                                                       |
| Individual Status  | Auto populated                                 |                                                                       |

**Effective Date:** July 19, 2024

```markdown
# Lab Results Tab

Relevant lab entries are automatically linked to current infection.
Do not primary organism until an organism is isolated and reported on the lab report.
Do not enter specimens not collected by the home.

## Linked Labs

| Primary | Culture Date | Results  | Organism  | Procedure            | Source       | Reason      | Collection Date | Lab ID   |
|---------|--------------|----------|-----------|----------------------|--------------|-------------|------------------|----------|
|         | 02-21-2023   | Positive | COVID-19  | Respiratory Culture   | Nasopharynx  | Symptomatic | 02-20-2023       | 2023-02  |

## Lab History

Culture Date Range: 01-24-2023 to 02-23-2023

| Culture Date | Results  | Organism  | Procedure            | Source       | Reason      | Collection Date | Lab ID   |
|--------------|----------|-----------|----------------------|--------------|-------------|------------------|----------|
| 02-21-2023   | Positive | COVID-19  | Respiratory Culture   | Nasopharynx  | Symptomatic | 02-20-2023       | 2023-02  |

----

# Treatments Tab

Do not use.

----

# Precautions Tab

Add and end precautions for each infection/colonization.

- Can end date in advance when initially entering infection case.

**Effective Date:** July 19, 2024
```

# Lab Results Module Rules

## New Lab Result Entry

- Enter all specimens collected, including urine, blood, any swab, stool, etc.
- Only enter one entry per specimen collected, including swab for respiratory culture.

| Field                | Filter Selection/Definition                   | Notes                                                                 |
|----------------------|----------------------------------------------|-----------------------------------------------------------------------|
| Individual type      | Select as appropriate                        |                                                                       |
| Facility             | Populated                                   |                                                                       |
| Unit                 | Select as appropriate                        |                                                                       |
| Individual           | Select as appropriate                        |                                                                       |
| Collection date      | Date specimen collected                      |                                                                       |
| Culture date         | Date specimen collected                      | Update the date to when result received                               |
| Procedure            | Select as appropriate                        | One lab entry per specimen, i.e., only enter one respiratory culture for FLUVID and MRVP |
| Result               | Select as appropriate                        | Do not enter refusals                                                |
|                      | PENDING – when waiting for results          | Do not leave PENDING for > 1 month – update as results are received  |
|                      | PRELIMINARY POSITIVE – POC DEVICE – positive RAT |                                                                       |
|                      | PRELIMINARY NEGATIVE – POC DEVICE – negative RAT |                                                                       |
| Organism             | Leave NOT SELECTED until organism is identified | Only select organism once identified/confirmed on lab                |
|                      | Select from drop down organism is isolated  | When selecting OTHER – add complete organism name to notes           |
| Source               | Select as appropriate                        |                                                                       |
|                      | SHALLOW ANTERIOR NARES - RATs              |                                                                       |
|                      | NASOPHARYNX – swabs collected for PCR respiratory testing |                                                       |
| Reason               | Select as appropriate                        |                                                                       |
| Lab ID               | Auto populated                              |                                                                       |
| Notes                | Use as appropriate                          |                                                                       |

If multiple organisms are identified from one swab, home will click on + sign to add additional organism to the same lab report.

| Result Code | Organism            | Positive | Procedure            | Source    | Reason     | Collection Date | Culture Date  |
|-------------|---------------------|----------|----------------------|-----------|------------|------------------|----------------|
| 0           | Metapneumovirus     | Yes      | Respiratory Culture   | NP swab   | Symptomatic| 2024-03-27       | 2024-03-29     |

**Effective Date:** 2024-03-27
**Review Date:** 2024-03-29
**Next Review Date:** July 19, 2024

# Outbreak Management Module

## New Outbreak Entry

Enter one outbreak per outbreak number provided by health unit or health authority.

| Field                | Filter Selection/Definition                                                                 | Notes                                                                                      |
|----------------------|--------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------|
| **+ New**            | Click on button to enter new outbreak                                                      |                                                                                            |
| **Infection Site**   | Select as appropriate                                                                      |                                                                                            |
| **Scope**            | Select as appropriate – can be adjusted from unit to facility if outbreak spreads        | If you select unit, you will only be able to add residents from that unit                 |
| **Causative Organism** | Select as appropriate                                                                    | If more than one organism is identified, enter the additional organisms in the notes section. DO NOT CREATE ANOTHER OUTBREAK |
| **Facility status**   | OPEN – open to admissions
HOME CLOSED – whole home closed to admissions
UNIT CLOSED – unit closed to admissions |                                                                                            | | |
| **Declared Date**     | Enter date outbreak declared                                                               |                                                                                            |
| **Resolved Date**     | Enter date declared over                                                                   |                                                                                            |
| **Confirmed**         | NO – for all suspect, enhanced surveillance, monitoring etc.
YES – select when outbreak is confirmed |                                                                                            | | |
| **Case Number**       | Enter outbreak number provided by health authority or public health                       |                                                                                            |
| **Case Definition**   | Enter case definition as determined with public health                                    | All residents meeting case definition will be confirmed                                    |
| **Notes**             | Use as appropriate to enter pertinent information                                          |                                                                                            |
| **Add**               | Click to add outbreak                                                                      |                                                                                            |

Once outbreak is created, complete Outbreak Checklist.

## Outbreak Summary

| Status      | Facility     | Scope        | Outbreak Type        | Causative Organism     | Facility Status | Date Declared | Date Resolved | First Case Date | Days In Outbreak | # of Cases | # of Residents |
|-------------|--------------|--------------|----------------------|------------------------|-----------------|---------------|----------------|------------------|------------------|------------|-----------------|
| Respiratory | Human Coronavirus | Unit Closed | 04-02-2024          |                        | 03-29-2024      |                |                |                  |                  |            |                 |

Outbreak Details: Group by Day, Week, Month, Quarter, Year.

Add cases to outbreak through Manage Infection Cases.

- Surveillance Report
- Export Data
- Manage Infection Cases
- New Case

*Page last updated: July 19, 2024*