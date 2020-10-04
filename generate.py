from binascii import hexlify
from hashlib import md5

import xml.dom.minidom
import argparse

from music21 import stream
from music21 import chord
from music21 import converter
from music21 import tinyNotation

parser = argparse.ArgumentParser()
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


def slugify(value, allow_unicode=False):
    """
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    import unicodedata
    import re
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')

def newsong(title, rh, rhf, lh, lhf, play=False):
    tnc = tinyNotation.Converter()
    class ChordState(tinyNotation.State):
        def affectTokenAfterParse(self, n):
           super(ChordState, self).affectTokenAfterParse(n)
           return None # do not append Note object

        def end(self):
            ch = chord.Chord(self.affectedTokens)
            ch.duration = self.affectedTokens[0].duration
            return ch

    tnc.bracketStateMapping['chord'] = ChordState
    tnc.bracketStateMapping['ch'] = ChordState
    sc = stream.Score()
    tnc.load(rh)
    tnc.parse()
    right_hand = tnc.stream
    #converter.parse("tinynotation:" + rh)
    right_hand_fing = rhf
    #left_hand = converter.parse ("tinynotation:" + lh)
    tnc.load(lh)
    tnc.parse()
    left_hand = tnc.stream
    left_hand_fing = lhf

    sc.append(right_hand)
    sc.append(left_hand)

    filename = slugify(title) + '.mid'
    sc.write('midi', fp=filename)
    sc.write('musicxml', fp=slugify(title) + '.mid')
    
    if play:
      sc.show('midi')

    with open(filename, 'rb') as f:
        s = f.read()

    md5_sig = hexlify(md5(s).digest()).decode("utf-8")

    def convert_fingers(s, right_hand):
        s1 = s.replace(' ','')
        def convert(c):
            if c == '-':
                return c
            else:
                n = int(c, 10)
                if right_hand:
                    n += 5
                n = n%10
                return str(n)
        s2 = ''.join(map(convert, s1))
        return s2


    # check if a song with the same title exists
    songlist = songs.getElementsByTagName('Song')
    for s in songlist:
        #print(s)
        if s.getAttribute('UniqueId') == md5_sig or s.getAttribute('Title') == title:
            #print('removing child')
            songs.removeChild(s)

    song = dom.createElement('Song')
    song.setAttribute('UniqueId', md5_sig)
    song.setAttribute('Title', title)
    song.setAttribute('FingerHints', 't0: {} t1:{}'.format(convert_fingers(right_hand_fing, True), convert_fingers(left_hand_fing, False)))
    song.setAttribute('Parts', 't0:RA t1:LA')
    song.setAttribute('Difficulty', '10')
    songs.appendChild(song)

newsong('Petit Poney', "4/4 r4 r  c  e    d2 c4 e    d2 c4 e    g f e d     e2 c4 e    d2 c4 e    d2 c4 e    g f e d    c2",
                       "          1  3    2  1  3    2  1  3    5 4 3 2     3  1  3    2  1  3    2  1  3    5 4 3 2    -",
                       "4/4  r1           G2 r       G2 r       G2 A4 B4    c2 r       G2 r       G2 r       G2 A4 B4   c2",
                       "                  4          4          4  3  2     1"
                       )

newsong('A vous dirais-je maman',
                       "4/4 r4 r  d  d    e e  d2    r4 r  r  r  r  r  r2  d4  d c c  r1       d4  d c c  r1       r4 r  d d e e d2  ",
                       "          2  2    3 3  2                           2   2 1 1           2   2 1 1                 2 2 3 3 2",
                       "4/4 G4 G  r  r    r r  r2    c4  c B  B  A  A  G2  r4  r r r  B  B A2  r1         B4 B A2  G4 G4 r1      r2  c4 c B B A A G2",
                       "    4  4                     1   1 2  2  3  3  4              2  2 3              2  2 3   4  4              1  1 2 2 3 3 4  "
                       )

newsong('BAJibC CPOHRT',
                       "3/4 r2 r4    c4 e g   d2.                g2.                f4  e  f  d2.                 r2 r4       r4 ch{c e g} ch{c e g}",
                       "             1  3 5   2                  5                  4   3  4  2                                     1 3 5     1 3 5",
                       "3/4 C4 E  G  r2 r4    r4 ch{F G} ch{F G} r4 ch{F G} ch{F G} r2 r4     r4 ch{F G} ch{F G}  G F# G      E2.",
                       "    5  3  1                2 1      2 1        2 1     2 1                  2 1     2 1   1 2  1      3"
                       ,play=False)

def pretty_print(doc):
    return '\n'.join([line for line in doc.toprettyxml(indent=' '*2, encoding='UTF-8').decode("utf-8").split('\n') if line.strip()])

with open(args.synthesiafile, 'w') as f:
    #dom.writexml(f, encoding='UTF-8', indent="", addindent="  ", newl="")
    f.write(pretty_print(dom))
    