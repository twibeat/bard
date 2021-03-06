# _*_ coding: utf-8 _*_
from music21 import note, stream, converter, midi
from fractions import Fraction
import numpy as np
import os
import glob
class MidiTool:
    def __init__(self, step=1, maxlen=16):
        """
		maxlen을 크게 하고 step의 수룰 줄이면 한음만 반복되는 현상이 줄어 들지만 학습이 느려진다.
		maxlen이라는 이름은 좀 그렇다. 한번에 학습시킬 멜로디의 수를 나타내는건데...
		"""
        self.maxlen = maxlen
        self.step = step

    def parse_midi(self, filename):
        """
		http://web.mit.edu/music21/doc/usersGuide/usersGuide_17_derivations.html	
		sample.mid는 불러오면 Score이고 여러개의 Part로 구성된다. Part는 Voice로 구성되어 있다.
		midi파일에서 최초의 Voice를 찾는다. 
		"""
        if not os.path.exists(filename):
            print("file is none")
            exit()

        print("parse midi file...")
        score = converter.parse(filename)
        header = stream.Part()
        for part in score:
            if len(part.voices) is 0:
                return self.process_no_voice(header, part)
            for voice in part:
                if isinstance(voice, stream.Voice):
                    print("length: ", len(voice))
                    return self.make_list(voice), header

        print("can not found notes!!")
        exit()

    def process_no_voice(self, header, part):
        voice = stream.Voice()
        for element in part:
            if isinstance(element, note.Note) or isinstance(element, note.Rest):
                voice.insert(element)
        if len(voice) is 0:
            print("can not found notes!")
            exit()
        return self.make_list(voice), header

    def make_list(self, stream):
        """
		voice는 note의 스트림임
		"""
        stream_to_list = []

        for each_item in stream:
            if isinstance(each_item, note.Note):
                stream_to_list.append(
                    each_item.name + str(each_item.octave) + '/' + str(each_item.duration.quarterLength))
            elif isinstance(each_item, note.Rest):
                stream_to_list.append(each_item.name + '/' + str(each_item.duration.quarterLength))

        return stream_to_list#, stream[0:header_size]

    def preprocess(self, sheet):
        self.make_table(sheet)
        self.mapping_data(sheet)
        x, y = self.onehotEncoding()
        return x, y, self.values;

    def make_table(self, sheet):
        self.values = sorted(list(set(sheet)))
        self.values_indices = dict((v, i) for i, v in enumerate(self.values))
        self.indices_values = dict((i, v) for i, v in enumerate(self.values))

    def mapping_data(self, sheet):
        """
		학습할 x(sentences) y(next_values)를 정한다.
		"""

        self.sentences = []
        self.next_values = []
        for i in range(0, len(self.values) - self.maxlen, self.step):
            self.sentences.append(sheet[i: i + self.maxlen])
            self.next_values.append(sheet[i + self.maxlen])

    def onehotEncoding(self):
        """
		데이터에 맞게 x,y를 만든다.
		"""
        x = np.zeros((len(self.sentences), self.maxlen, len(self.values)), dtype=np.bool)
        y = np.zeros((len(self.sentences), len(self.values)), dtype=np.bool)

        for number, sentence in enumerate(self.sentences):
            for index, value in enumerate(sentence):
                x[number, index, self.values_indices[value]] = 1
            y[number, self.values_indices[self.next_values[number]]] = 1

        return x, y

    def out_midi(self, dir, header, chords):
        """생성된 char형태의 코드를 midi로 만들어줌"""
        score = stream.Score()
        part = stream.Part()

        for head in header:
            part.insert(head)

        voice = self.string_to_stream(chords)

        part.insert(voice)
        score.insert(part)
        self.write_stream(dir, score)

    def string_to_stream(self, chords):
        voice = stream.Voice()
        for chord in chords:
            # 현재는 (음과 옥타브 / 음길이) 형태로 구분한다. 나누어 준다.
            chord = chord.split('/', 1)
            if chord[0] == "rest":
                n = note.Rest(chord[0])
                n = self.set_duration(n, chord[1])
            else:
                n = note.Note(chord[0])
                n = self.set_duration(n, chord[1])
            voice.append(n)
        return voice

    def write_stream(self, dir, streams):
        """stream을 저장한다."""
        print("write stream...")
        midi_file = midi.translate.streamToMidiFile(streams)
        midi_file.open(dir, 'wb')
        midi_file.write()
        midi_file.close()

    def set_duration(self, note, duration):
        """
		무한 소수 같은건 (1/12) 분수로 표현되어서 이에 대한 처리를 해준다. python3쓰면 상관이 없긴한데 ...
		기본 모듈 중 하나인 Fraction(from fractions import Fration) 이용
		"""
        if duration.find('/') is not -1:
            splited = duration.split('/')
            note.duration.quarterLength = Fraction(int(splited[0]), int(splited[1]))
        else:
            note.duration.quarterLength = float(duration)
        return note
