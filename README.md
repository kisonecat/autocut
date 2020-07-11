# Autocut

I needed a way to make videos for my [Calculus
MOOC](http://mooculus.osu.edu/) very quickly, and so I build the
`autocut`ter.

This tool takes a list of video files, listens to the audio to
determine where I start and stop speaking, and builds an edit list
suitable for [MLT](https://github.com/mltframework/mlt).

If you want help using it, please feel free to contact me.

## Requirements

This is a python script packaged using `setuptools`.  The
[numpy](https://github.com/numpy/numpy) and
[librosa](https://github.com/librosa/librosa) libraries are used.
The python code also depends on
[MLT](https://github.com/mltframework/mlt) being installed.

## Instructions

Here is a sample input file.  Let's call it `sample.xml`

    <?xml version="1.0" encoding="UTF-8"?>
    <movie author="Jim Fowler">
      <video src="title.mp4" audio="intro.wav" in="0" out="3"/>
      <video src="welcome-to-the-course.mts"/>
      <video src="doing-work-on-paper.mts" flip="true"/>
      <video src="farewell-everybody.mts"/>
      <video src="end-title.mp4" audio="outro.wav" in="0" out="5"/>
    </movie>

If you run `autocut sample.xml` you will get `editlist.xml`
which you can then run through `melt` to produce a complete video.

The `in` and `out` timestamps are in seconds, relative to the given
video file.  If you don't include one of them, then the missing
cutpoints are determined by listening for a human voice.

If you include a `flip` attribute, the video gets flipped.

If you include an `audio` tag, then the given audio file will play at
the same time as the given video; the script creates the appropriate
tractors and transitions to mix the audio in MLT.
