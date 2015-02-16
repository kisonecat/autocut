#! /usr/bin/ruby
# 
# autocut.rb - automatically cut off the parts of the video where I'm not speaking
# 
# Jim Fowler <fowler@math.osu.edu>
# 

require 'fftw3'
require 'tempfile'
require 'wavefile'
include WaveFile 
require 'xml'

################################################################
# determine where I start and stop speaking

SAMPLES_PER_BUFFER = 2048

def find_audio_cut_points(wave_filename)
  info = Reader.info(wave_filename)
  maximum_amplitude = 2**(info.bits_per_sample - 1)

  duration_in_seconds = info.duration.hours * 3600 + info.duration.minutes * 60 + info.duration.seconds + info.duration.milliseconds/1000.0

  first_loud_moment = nil
  last_loud_moment = nil

  # Depending on the fundamental frequency of your voice, you may want to change this
  frequency_window = 100..300

  # my chair tended to squeak in this range
  anti_frequency_window = 850..900
  maximum = nil

  index = 0
  Reader.new(wave_filename).each_buffer(SAMPLES_PER_BUFFER) do |buffer|
    next if buffer.samples.length < SAMPLES_PER_BUFFER
    seconds = (index).to_f / info.sample_rate
    index = index + SAMPLES_PER_BUFFER
    next if seconds < 1.0

    na = NArray.to_na(buffer.samples)
    fft = FFTW3.fft(na).to_a[0, SAMPLES_PER_BUFFER/2]
    fft = fft.map(&:abs)

    total = 0.0
    for i in frequency_window
      total = total + fft[i]
    end

    antitotal = 0.0
    for i in anti_frequency_window
      antitotal = antitotal + fft[i]
    end

    if maximum.nil? or total > maximum
      maximum = total
    end
  end

  index = 0
  Reader.new(wave_filename).each_buffer(SAMPLES_PER_BUFFER) do |buffer|
    next if buffer.samples.length < SAMPLES_PER_BUFFER

    na = NArray.to_na(buffer.samples)
    fft = FFTW3.fft(na).to_a[0, SAMPLES_PER_BUFFER/2]
    fft = fft.map(&:abs)

    total = 0.0
    for i in frequency_window
      total = total + fft[i]
    end

    seconds = (index).to_f / info.sample_rate
    index = index + SAMPLES_PER_BUFFER
    next if seconds < 0.3
    #next if seconds > (duration_in_seconds - 1.5)

    if total > 0.2 * maximum      
      if first_loud_moment.nil? or seconds < first_loud_moment
        first_loud_moment = seconds
      end
      
      if last_loud_moment.nil? or seconds > last_loud_moment
        last_loud_moment = seconds
      end
    end
    
  end

  return first_loud_moment..last_loud_moment
end

def find_video_cut_points(movie_filename)
  filename1 = Tempfile.new(['movie-audio-one','.wav'])
  filename2 = Tempfile.new(['movie-audio-two','.wav'])
  system( "ffmpeg -y -i #{movie_filename} -vn -ac 1 -ar 44100 -f wav #{filename1.path} 2>/dev/null" )
  # I am not sure why FFTW is happier if I run the audio through sox
  system( "sox #{filename1.path} #{filename2.path}" )
  return find_audio_cut_points(filename2.path)
end

################################################################
# load videos from the XML file

videos = []

input_parser = XML::Parser.file( ARGV[0] )
doc = input_parser.parse
for video in doc.find('/movie/video')
  videos << video
end

for video in videos
  if video['in'].nil? or video['out'].nil?
    puts "Listening to #{video['src']}..."
    cuts = find_video_cut_points( video['src'] )
    # attributes must be strings, not floats, unfortunately
    video['in'] ||= (cuts.first - 0.30).to_s
    video['out'] ||= (cuts.last + 0.35).to_s
    puts video
  end

  if video['id'].nil?
    video['id'] = video['src'].gsub( /\..*/, '' )
  end
end

f = File.open("editlist.xml","w")

f.puts "<mlt>"

for video in videos
  f.puts "  <producer id=\"#{video['id']}-source\">"
  f.puts "    <property name=\"resource\">#{video['src']}</property>"
  f.puts "  </producer>"

f.puts <<EOF
    <tractor id="#{video['id']}">
       <multitrack>
         <track producer="#{video['id']}-source"/>
       </multitrack>
EOF

  unless video['flip'].nil?
    f.puts <<EOF
       <filter>
         <property name="track">0</property>
         <property name="mirror">flip</property>
         <property name="mlt_service">mirror</property>
       </filter>
       <filter>
         <property name="track">0</property>
         <property name="mirror">flop</property>
         <property name="mlt_service">mirror</property>
       </filter>
EOF
  end
  f.puts "    </tractor>"
end

################################################################
# add producers for extra audio tracks

for video in videos
  unless video['audio'].nil?
f.puts <<EOF
  <producer id="#{video['id']}-audio">
    <property name="resource">#{video['audio']}</property>
    <property name="normalise"></property>
  </producer>
EOF
  end
end

################################################################
# write main playlist, storing starting frames along the way

playlist = "main-playlist"
f.puts "  <playlist id=\"#{playlist}\">"

scene_start = 0

for video in videos

  melted = `melt #{video['src']} -consumer xml`
  parser = XML::Parser.string(melted)
  doc = parser.parse
  frame_rate_num = doc.find('profile')[0]['frame_rate_num'].to_i
  frame_rate_den = doc.find('profile')[0]['frame_rate_den'].to_i
  frame_rate_num = 90000
  frame_rate_den = 1501
  frame_rate = frame_rate_num.to_f / frame_rate_den.to_f
  frame_rate = 30.0

  cut_in = ((video['in'].to_f) * frame_rate).floor
  cut_out = ((video['out'].to_f) * frame_rate).ceil

  video['start'] = scene_start.to_s
  scene_length = cut_out - cut_in
  scene_start = scene_start + scene_length

  f.puts "    <entry producer=\"#{video['id']}\" in=\"#{cut_in}\" out=\"#{cut_out}\"/>"
end

f.puts "  </playlist>"

total_frames = scene_start

################################################################
# make playlists to mix together the extra audio tracks

for video in videos
  unless video['audio'].nil?
f.puts <<EOF
  <playlist id="#{video['id']}-audio-playlist">
    <blank length="#{video['start']}"/>
    <entry producer="#{video['id']}-audio" out="#{total_frames - video['start'].to_i}"/>
  </playlist>

  <tractor id="#{playlist}-mix">
    <multitrack>
      <track producer="#{playlist}"/>
      <track producer="#{video['id']}-audio-playlist"/>
    </multitrack>
    <transition id="transition-#{playlist}" out="#{total_frames}">
      <property name="a_track">0</property>
      <property name="b_track">1</property>
      <property name="mlt_type">transition</property>
      <property name="mlt_service">mix</property>
    </transition>
  </tractor>
EOF

    playlist = playlist + "-mix"
  end
end

f.puts "</mlt>"
f.close

