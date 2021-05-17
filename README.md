# vCard-parser

vCard-parser is a simple python script that parses a vCard (.vcf) file and outputs the data
in a printable/human-readable way. It is useful when you need to save your contacts
on a computer or print them.

### Usage (assuming [python](https://www.python.org/) is installed) :
```sh
python export.py <input_filename> <output_filename>
```
### Features to be added:
- Another script that just displays info about the vCard file
- Verbose mode
- Export to .csv (or any Excel compatible file type)

#### Error exit codes:
- -1: problem parsing the arguments
-  2: unexpected charset (non utf-8) detected
-  3: input file not found

#### How the script works:
The script reads the input file line-by-line, handling each line according to the label
that it begins with. A dictionary is created for each contact, and its information is stored
in there. The dictionary is formatted as follows:
- full_name: string
- name info: dictionary
- nickname: string
- organization: string
- phone numbers: dictionary
- email addresses: dictionary
- birthday: string
- revision date: string

Once all the information about a single contact is collected, the contact is added to a list.
When all the contacts in the input file are added to that list, the script iterates through it
and writes each contact's information to the output file.
