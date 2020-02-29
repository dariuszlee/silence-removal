#! /usr/bin/env python
# encoding: utf-8



import numpy
import scipy.io.wavfile as wf
import sys

## number of ms of silence before selecting a new segment 
ms = 1000

class VoiceActivityDetection:

    def __init__(self, sr, ms, channel, output_path):
        self.__output_path = output_path
        self.__sr = sr
        self.__channel = channel
        self.__step = int(sr/50)
        self.__buffer_size = int(sr/50)
        self.__buffer = numpy.array([],dtype=numpy.int16)
        self.__out_buffer = numpy.array([],dtype=numpy.int16)
        self.__n = 0
        self.__VADthd = 0.
        self.__VADn = 0.
        self.__silence_counter = 0
        self.__segment_count = 0
        self.__voice_detected = False
        self.__silence_thd_ms = ms

    # Voice Activity Detection
    # Adaptive threshold
    def vad(self, _frame):
        frame = numpy.array(_frame) ** 2.
        result = True
        threshold = 0.1
        thd = numpy.min(frame) + numpy.ptp(frame) * threshold
        self.__VADthd = (self.__VADn * self.__VADthd + thd) / float(self.__VADn + 1.)
        self.__VADn += 1.

        if numpy.mean(frame) <= self.__VADthd:
            self.__silence_counter += 1
        else:
            self.__silence_counter = 0

        if self.__silence_counter > self.__silence_thd_ms*self.__sr/(1000*self.__buffer_size):
            result = False
        return result

    # Push new audio samples into the buffer.
    def add_samples(self, data):
        self.__buffer = numpy.append(self.__buffer, data)
        result = len(self.__buffer) >= self.__buffer_size
        # print('__buffer size %i'%self.__buffer.size)
        return result

    # Pull a portion of the buffer to process
    # (pulled samples are deleted after being
    # processed
    def get_frame(self):
        window = self.__buffer[:self.__buffer_size]
        self.__buffer = self.__buffer[self.__step:]
        # print('__buffer size %i'%self.__buffer.size)
        return window

    # Adds new audio samples to the internal
    # buffer and process them
    def process(self, data):
        if self.add_samples(data):
            while len(self.__buffer) >= self.__buffer_size:
                # Framing
                window = self.get_frame()
                # print('window size %i'%window.size)
                if self.vad(window):  # speech frame
                    self.__out_buffer = numpy.append(self.__out_buffer, window)
                    self.__voice_detected = True
                elif self.__voice_detected:
                    self.__voice_detected = False
                    self.__segment_count = self.__segment_count + 1
                    wf.write('%s.%i.%i.wav' % (self.__output_path, self.__channel,self.__segment_count), self.__sr, self.__out_buffer)
                    self.__out_buffer = numpy.array([],dtype=numpy.int16)

                # print('__out_buffer size %i'%self.__out_buffer.size)

    def get_voice_samples(self):
        return self.__out_buffer
 

def segmentize(wav_file, output):
    wav = wf.read(wav_file)
    ch = wav[1].shape[1]
    sr = wav[0]

    c0 = wav[1][:,0]

    print('c0 %i'%c0.size)

    vad = VoiceActivityDetection(sr, ms, 1, output)
    vad.process(c0)

    # if ch==1:
    #     return
        
    # vad = VoiceActivityDetection(sr, ms, 2)
    # c1 = wav[1][:,1]
    # vad.process(c1)

def main():
    segmentize(sys.argv[1], sys.argv[2])

if __name__ == "__main__":
    main()
