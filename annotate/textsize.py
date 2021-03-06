# ./bin/env python3
# textlength.py
# author: #cf

"""
# Extract text length and other possible data from XML files and writes it back
"""

import glob
import os
import re

###############
## FUNCTIONS ##
###############

def main(basic_wdir, input_wdir, output_wdir, mode):
    """
        Example of how to use it:
        main("/home/jose/cligs/ne/","master/*.xml", "master/", "structure")
    """

    # The we open each file
    for doc in glob.glob(basic_wdir+input_wdir):
        idno_file = os.path.basename(doc)
        print(idno_file)
        with open(doc, "r", errors="replace", encoding="utf-8") as fin:
            content = fin.read()

            # Size in kb is calculated            
            size_kb = str(int(os.path.getsize(doc)/1024))
            
            # From the TEI File, teiHeader, front and back are deleted
            content_body = content
            content_body = re.sub(r'<teiHeader>.*?</teiHeader>', r'', content_body, flags=re.DOTALL)
            content_body = re.sub(r'<front>.*?</front>', r'', content_body, flags=re.DOTALL)
            content_body = re.sub(r'<back>.*?</back>', r'', content_body, flags=re.DOTALL)
            
            # Divs and groups of lines are counted
            divs = str(content_body.count("<div"))
            lines = str(len(re.findall(r'\n+',content_body)))

            
            # if we want also structure
            if mode == "structure":
                
                # Diferent TEI elements are counted
                chapters = str(len(re.findall(r'<div\s+type="chapter"',content_body)))
                blocks = str(len(re.findall(r'<(l|ab|head|stage|sp|p|ab)( .+?|)>',content_body)))
                line_verses = str(len(re.findall(r'<(l)( .+?|)>',content_body)))
                heads = str(len(re.findall(r'<(head)( .+?|)>',content_body)))
                stages = str(len(re.findall(r'<(stage)( .+?|)>',content_body)))
                sps = str(len(re.findall(r'<(sp)( .+?|)>',content_body)))
                ps = str(len(re.findall(r'<(p)( .+?|)>',content_body)))
                abs_ = str(len(re.findall(r'<(ab)( .+?|)>',content_body)))
                ft = str(len(re.findall(r'<(floatingText)( .+?|)>',content_body)))
                
                # The paragraphas that have right after a punctuation mark that presents direct speech are counted
                speech_ps = str(len(re.findall(r'<(p)( .+?|)> ?(<[^>]*?>)? *[-—–~»«]',content_body)))

            # Then the text is converted into plaintext and the white space cleaned
            plain_body = content_body
            plain_body = re.sub(r'</?.*?>', r'', plain_body, flags=re.DOTALL)
            plain_body = re.sub(r'[\t ]+', r' ', plain_body)
            plain_body = re.sub(r'\n[\n]+', r'\n', plain_body)

            # Characters and words are counted
            chars = str(len(plain_body))
            words = str(len(re.findall(r'[\wáéíóúñü\d]+',plain_body)))


            # If we want some more info, the ammount of numbers and punctuation marks are counted
            if mode == "structure":
                numbers = str(len(re.findall(r'\d+',plain_body)))
                puncts = str(len(re.findall(r'[!"\#$%&\'()*+,\-./:;<=>?@\[\\\]^_`{|}~¿¡…—–~»«]',plain_body)))
            

            # All this information is written in the TEI             
            content = re.sub(r'\s+<extent>.*</extent>', r'', content, flags=re.DOTALL)

            content = re.sub(r'(\n[\s\t]+<publicationStmt>)', r'\n\t\t\t<extent>\n\t\t\t\t<measure unit="lines">'+re.escape(lines)+r'</measure>\n\t\t\t\t<measure unit="divs">'+re.escape(divs)+r'</measure>\n\t\t\t\t<measure unit="words">'+re.escape(words)+r'</measure>\n\t\t\t\t<measure unit="chars">'+re.escape(chars)+r'</measure>\n\t\t\t\t<measure unit="size_kb">'+re.escape(size_kb)+r'</measure>\n\t\t\t</extent>\1', content, flags=re.DOTALL)
            if mode == "structure":
                content = re.sub(r'(\s+</extent>)', r'\n\n\t\t\t\t<measure unit="chapters">'+re.escape(chapters)+r'</measure> \n\t\t\t\t<measure unit="blocks">'+re.escape(blocks)+r'</measure> \n\t\t\t\t<measure unit="line_verses">'+re.escape(line_verses)+r'</measure> \n\t\t\t\t<measure unit="heads">'+re.escape(heads)+r'</measure> \n\t\t\t\t<measure unit="stages">'+re.escape(stages)+r'</measure> \n\t\t\t\t<measure unit="sps">'+re.escape(sps)+r'</measure> \n\t\t\t\t<measure unit="paragraphs">'+re.escape(ps)+r'</measure> \n\t\t\t\t<measure unit="abs">'+re.escape(abs_)+r'</measure> \n\t\t\t\t<measure unit="floatingTexts">'+re.escape(ft)+r'</measure>\n\t\t\t\t<measure unit="paragraphs_ds">'+re.escape(speech_ps)+r'</measure> \n\t\t\t\t<measure unit="numbers">'+re.escape(numbers)+r'</measure> \n\t\t\t\t<measure unit="puncts">'+re.escape(puncts)+r'</measure>\1', content)

            # The file is written
            with open (os.path.join(basic_wdir+output_wdir, idno_file), "w", encoding="utf-8") as fout:
                fout.write(content)
                
main("/home/ulrike/Git/textbox/spanish/novela-hispanoamericana/", "tei/*.xml", "tei2/", "default")
