import os
import argparse
from binascii import hexlify
from hashlib import md5
from itertools import zip_longest

import xml.dom.minidom

from music21 import converter
from music21.note import Note
from music21.chord import Chord
from music21.articulations import Fingering

parser = argparse.ArgumentParser()
parser.add_argument("musicxmlfile", help="musicxmlfile to import and add as midi to synhesia file")
parser.add_argument("synthesiafile", help="synthesia file to update")
args = parser.parse_args()

try:
    dom = xml.dom.minidom.parse(args.synthesiafile)
    songs = dom.getElementsByTagName('Songs')[0]
except FileNotFoundError:
    print('Creating new file')
    dom = xml.dom.minidom.getDOMImplementation().createDocument(None, "SynthesiaMetadata", None)
    dom.documentElement.setAttribute('Version', '1')
    songs = dom.createElement('Songs')
    metadata = dom.getElementsByTagName('SynthesiaMetadata')[0]
    dom.documentElement.appendChild(songs)

#print(dom.toprettyxml(encoding='UTF-8'))


# read the music xml file
score = converter.parse(args.musicxmlfile, format='musicxml')
# replace the extension of the file with mid
filename = os.path.splitext(args.musicxmlfile)[0]+'.mid'
score.write('midi', fp=filename)

with open(filename, 'rb') as f:
    s = f.read()

md5_sig = hexlify(md5(s).digest()).decode("utf-8")

# check if a song with the same unique id exists
songlist = songs.getElementsByTagName('Song')
for s in songlist:
    #print(s)
    if s.getAttribute('UniqueId') == md5_sig or s.getAttribute('Title') == title:
        #print('removing child')
        songs.removeChild(s)

song = dom.createElement('Song')
song.setAttribute('UniqueId', md5_sig)
song.setAttribute('Title', score.metadata.title)
righthandpart = score.parts[0]
lefthandpart = score.parts[1]

def finger_list(notes, isRightHand):
    def convert_finger(finger):
        if finger != None:
            if isRightHand:
                return str((finger + 5) % 10)
            else:
                return str(finger)
        else:
            return '-'

    fingerlist = ""
    for note in notes:
        if isinstance(note, Note):
            # find the first finger information
            finger = next((a.fingerNumber for a in note.articulations if isinstance(a, Fingering)), None)
            fingerlist += convert_finger(finger)
        elif isinstance(note, Chord):
            chord = note
            # get all the finger information corresponding to the chord
            fingers = filter(lambda x: isinstance(x, Fingering), chord.articulations)
            # for a chord, we must generate the appropriate number of notes even if it is not provided
            for chordNote, finger in zip_longest(chord.notes, fingers):
                if finger != None:
                    finger = finger.fingerNumber
                fingerlist += convert_finger(finger)
    return fingerlist

rh = finger_list(righthandpart.flat.notes, True)
lh = finger_list(lefthandpart.flat.notes, False)

song.setAttribute('FingerHints', 't0: {} t1:{}'.format(rh, lh))
song.setAttribute('Parts', 't0:RA t1:LA')
song.setAttribute('Difficulty', '10')
songs.appendChild(song)


def pretty_print(doc):
    return '\n'.join([line for line in doc.toprettyxml(indent=' '*2, encoding='UTF-8').decode("utf-8").split('\n') if line.strip()])

with open(args.synthesiafile, 'w') as f:
    #dom.writexml(f, encoding='UTF-8', indent="", addindent="  ", newl="")
    f.write(pretty_print(dom))
    