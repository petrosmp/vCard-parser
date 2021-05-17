import sys
import time
import re
from copy import deepcopy

# get the input file's name from the arguments
try:
    path = sys.argv[1]
except IndexError:
    print("Usage: python extract.py <input_filename> <output_filename>")
    exit(-1)

# try to get the output file's name from the arguments
try:
    outfile = sys.argv[2]
except IndexError:
    print("Usage: python extract.py <input_filename> <output_filename>")
    exit(-1)

# open file
try:  
    src = open(path, "rb+") 
except FileNotFoundError:
    print("File not found! Are you sure you entered the file name correctly?")
    exit(3)


element_desc = ["lastname", "firstname", "middlename", "honPref", "honPost"]
name_elements = {}
contacts = []
contact = {}
tel = {}
emails = {}

# iterate through the lines of the file
while(True):
    line = src.readline().strip().decode("utf-8", "replace")
    if(not line): 
        break
    
    if "BEGIN:VCARD" in line:
        # here the last vCard has ended, so we need to add it to the list
        if(tel):
            contact.update({"phone numbers": deepcopy(tel)})
            tel.clear()
        if(emails):
            contact.update({"email addresses": deepcopy(emails)})
            emails.clear()
        if(contact):
            contacts.append(deepcopy(contact))
            contact.clear()
        pn_counter = 1
        em_counter = 1
        
        # here the vCard is iterated through
        while "END:VCARD" not in line:
            # each line is read and decoded (some characters might be read as bytes)
            # or fail to be mapped to ascii ones otherwise
            line = src.readline().strip().decode("utf-8", "replace")
            
            # the following labels are skipped (because they are useless to humans)
            if "END:VCARD" in line or "VERSION" in line or "PRODID" in line:
                continue
            
            # the label if the first part of the line. It describes
            # the info that follows. It is what we use to sort and decide
            # how to handle the information we find
            label = line.partition(":")[0].strip().replace(";", " ")
            data = line.partition(":")[2].strip()
            """
            Case #1:    The information is labeled N or N;CHARSET

                In this case, we store the name related info in a properly 
                formatted dictionary (called name_elements{}).
                
                A name field should look something like this:
                N;CHARSET="utf-8": John;Doe;MiddleName;;;
                (this is the format described at https://www.w3.org/TR/vcard-rdf/)
                
                However, noone saves all his contacts correctly, so a lot
                of weird formats are expected. We can do nothing to sort
                these out, since there is no way to know a priori what is a 
                name, what is a surname and so on.
            """
            if (label[0]=='N') and ("NOTE" not in label):
                data = data.split(';')
                for count, item in enumerate(data):
                    if(data[count]):
                        name_elements.update({element_desc[count]: data[count]})
                

                contact.update({"name info": deepcopy(name_elements)})
                name_elements.clear()

                # we also need to display the appropiate message in the case of the 
                # charset not being UTF-8
                if("CHARSET=" in label):
                    charset = label.split("=")[1]
                    if(charset.lower()!="utf-8"):
                        print(f"Invalid charset detected at contact {data}")
                        exit(2)

            """
            Case #2:    The information is labeled FN or FN;CHARSET

                In this case, we just create another entry in the contact's
                dictionary. The key is "formatted name" and the value is
                the information that follows the label. It is usually all of
                the components of the name field, concatenated.
            """ 
            if(label.startswith("FN")):
                if(data):
                    contact.update({"formatted name": data})

                # we also need to display the appropiate message in the case of the 
                # charset not being UTF-8
                if("CHARSET=" in label):
                    charset = label.split("=")[1]
                    if(charset.lower()!="utf-8"):
                        print(f"Invalid charset detected at contact {data}")
                        exit(2)

            """
            Case #3:    The information is labeled NICKNAME or NICKNAME;CHARSET

                In this case, we just create another entry in the contact's
                dictionary. The key is "nickname" and the value is the
                information that follows the label. It is quite rare.
            """
            if(label.startswith("NICKNAME")):
                if(data):
                    contact.update({"nickname": data})

                # we also need to display the appropiate message in the case of the 
                # charset not being UTF-8
                if("CHARSET=" in label):
                    charset = label.split("=")[1]
                    if(charset.lower()!="utf-8"):
                        try:
                            print(f"Invalid charset detected at contact {name_elements['formatted name']}")
                            exit(2)
                        except:
                            print(f"Inavlid charset detected at contact {data}")
                            exit(2)

            """
            Case #4:    The information is labeled TITLE

                In this case, we just create another entry in the contact's
                dictionary. The key is "title" and the value is the information
                that follows the label. It is also quite rare.
            """
            if(label.startswith("TITLE")):
                if(data):
                    contact.update({"title": data})
            
            """
            Case #5:    The information is labeled X-IMAGETYPE

                In this case, we just create another entry in the contact's
                dictionary. The key is "image type" and the value is the information
                that follows the label. It is also quite rare but we have to
                account for it.
            """
            if(label.startswith("X-IMAGETYPE")):
                if(data):
                    contact.update({"image type": data})
            
            """
            Case #6:    The information is labeled REV

                According to https://www.w3.org/TR/vcard-rdf/, the REV label refers
                to the date that the contact was revised. This sounds like something
                that should be created automatically everytime a contact is created/
                altered and thus be present in all contacts. However it seems that 
                few contacts actually have it. Nevertheless, we treat it just like 
                any other label.

                We  create another entry in the contact's dictionary. The key is 
                "revision date" and the value is the information that follows the 
                label.
            """
            if(label.startswith("REV")):

                # The datetime format that seems to be used in every occurence of 
                # the REV prefix (YYYY-MM-DD<T>HH:MM:SS<Z>) is explained here 
                # https://stackoverflow.com/a/8405125 and here https://en.wikipedia.org/wiki/ISO_8601
                # The following changes are made according to information from 
                # the above links in order to improve readability.
                data = data.replace("T", ", ").replace("Z", " UTC")
                if(data):
                    contact.update({"revision date": data})
            
            """
            Case #7:    The information is labeled ORG

                In this case, we just create another entry in the contact's
                dictionary. The key is "organization" and the value is the information
                that follows the label. It is also quite rare.
            """
            if(label.startswith("ORG")):
                if(data):
                    contact.update({"organization": data})

            """
            Case #8:    The information is label BDAY

                In this case, we just create another entry in the contact's
                dictionary. The key is "birthday" and the value is the information
                that follows the label. It is also quite rare.
            """
            if(label.startswith("BDAY")):
                if(data):
                    contact.update({"birthday": data})

            """
            Case #9:    The information is labeled TEL, item1.TEL or item2.TEL

                This means that a phone number is to be expected after the label.
                A contact may have more than one phone numbers though, and usually
                when that happens, one of them is the "preffered" one. There are 
                also a bunch of different info that can be stored in a TEL label,
                like if the number is a cellphone, a home or work number, if it
                is voice, fax, or anything else etc (see https://www.w3.org/TR/vcard-rdf/).

                Those are all fields that we usually ignore when storing a 
                new contact, but they may be useful in some ways we dont know. 
                Anyway, we need to handle them propely.

                We create for each contact a dictionary (tel{}), in which we store
                the contact's numbers and info about those numbers as follows:
                tel = {
                    'mobile number'         : 'XXXXXXXXXX',
                    'home (voice) number'   : '+XX XXXXXXXXXX'
                }
                This dictionary is added to the contact dictionary when the next
                contact is found (see lines 41-53) with the key "phone numbers".

                The keys of the items in the tel{} dictionary are created in a dumb
                way and are derived from the context of the TEL label. There are also
                more codes that may be found and have to be taken into consideration
                (see https://www.w3.org/TR/vcard-rdf/, section 2.11).
            """
            if(label.startswith("TEL") or label.startswith("item1.TEL") or label.startswith("item2.TEL")):
                data = re.sub("[^\d \+]", "", data)   # remove anything that is not a digit, a space or a plus sign

                tel_info = ""
                if("pref" in label):
                    tel_info += "preferred "
                if("HOME" in label):
                    tel_info += "home "
                if("WORK" in label):
                    tel_info += "work "
                if("CELL" in label):
                    tel_info += "mobile "
                if("VOICE" in label):
                    tel_info += "(voice) "
                tel_info = tel_info.strip()
                label = f"{tel_info} number"
                label = label.strip()
                try:
                    if(tel[label]):
                        pn_counter+=1
                        label+=str(pn_counter)
                        tel.update({label: data})
                except KeyError:
                    tel.update({label: data})

            """
            Case #10:   The information is labeled EMAIL

                The same procedure with the TEL label is followed. The dictionary is
                named emails{}, and it's appended in the contact's dictionary in 
                line 47, with the key "email addresses".
            """
            if(label.startswith("EMAIL")):
                
                email_info = ""
                if("HOME" in label.upper()):
                    email_info += "home "
                if("pref" in label.lower()):
                    email_info += "preferred "
                # INTERNET tag means nothing
                if("WORK" in label.upper()):
                    email_info += "work "
                email_info = email_info.strip()
                label = f"{email_info} address"
                try:
                    if(emails[label]):
                        em_counter+=1
                        label+=str(em_counter)
                        emails.update({label: data})
                except KeyError:
                    emails.update({label: data})

            """
            Case #11:   The information is labeled NOTE
            """
            if(label.startswith("NOTE")):
                data = data.replace(r"\n", " newline ")
                # remember when printing notes to replace the " newline "s with legit "\n"'s

                contact.update({"notes": data})
                # we also need to display the appropiate message in the case of the 
                # charset not being UTF-8
                if("CHARSET=" in label):
                    charset = label.split("=")[1].split(' ')[0]
                    if(charset.lower()!="utf-8"):
                        try:
                            print(f"Invalid charset detected at contact {contact['formatted name']}")
                            exit(2)
                        except:
                            exit(2)
"""
Write the information to the file. The labels are in greek and can be changed in lines:
    > 333
    > 344
    > 349
    > 354
    > 362
    > 368
    > 390
    > 397
    > 405
"""
# open the file (if a file already exists, it will be overwritten)
out = open(outfile, "w+", encoding="utf-8")

for person in contacts:
    # print the full, formatted name
    try:
        full_name = person["formatted name"]
        out.write(f"Ονοματεπώνυμο: {full_name}\n")
    except KeyError:
        pass
    
    # print the name elements one by one
    try:
        # this is done extremely stupidly because i want the
        # name to be first and im way too bored to do it any 
        # other way
        names = person["name info"]
        try:
            out.write(f"Όνομα: {names['firstname']}\n")
        except KeyError:
            pass
        
        try:
            out.write(f"Middle Name: {names['middlename']}\n")
        except KeyError:
            pass
        
        try:
            out.write(f"Επώνυμο: {names['lastname']}\n")
        except KeyError:
            pass
    except KeyError:
        pass

    # print the nickname
    try:
        out.write(f"Ψευδώνυμο: {person['nickname']}\n")
    except KeyError:
        pass

    # print the organization
    try:
        out.write(f"Οργανισμός: {person['organization']}\n")
    except KeyError:
        pass

    # print the phone numbers
    try:
        phone_nums = person['phone numbers']
        for description, number in phone_nums.items():
            out.write(f"{description.capitalize()}: {number}\n")
    except KeyError:
        pass
    
    # print the emails
    try:
        email_addrs = person["email addresses"]
        for description, address in email_addrs.items():
            out.write(f"{description.capitalize()}: {address}\n")
    except KeyError:
        pass

    # print birthday
    try:
        out.write(f"Γενέθλια: {person['birthday']}\n")
    except KeyError:
        pass

    # print notes
    try:
        note = person["notes"].replace(" newline ", "\n\t")
        out.write("Σημειώσεις: ")
        out.write(f"\t{note}\n")
    except KeyError:
        pass

    # print revision date & time
    try:
        rev = person["revision date"]
        out.write(f"Τελευταία τροποποίηση: {rev}\n")
    except KeyError:
        pass
    
    #print a newline after each contact
    out.write("\n")