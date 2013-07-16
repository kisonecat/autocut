require 'fftw3'
require 'tempfile'
require 'wavefile'
include WaveFile 
require 'xml'

SAMPLES_PER_BUFFER = 2048

def find_audio_cut_points(wave_filename)
  info = Reader.info(wave_filename)
  maximum_amplitude = 2**(info.bits_per_sample - 1)

  duration_in_seconds = info.duration[:hours] * 3600 + info.duration[:minutes] * 60 + info.duration[:seconds] + info.duration[:milliseconds]/1000.0

  first_loud_moment = nil
  last_loud_moment = nil

  # Depending on the fundamental frequency of your voice, you may want to change this
  frequency_window = 50..150   
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
    next if seconds < 1.0
    next if seconds > (duration_in_seconds - 1.5)

    if total > 0.2 * maximum      
      if first_loud_moment.nil? or seconds < first_loud_moment
        first_loud_moment = seconds
      end
      
      if last_loud_moment.nil? or seconds > last_loud_moment
        last_loud_moment = seconds
      end
    end
    
  end

  return [first_loud_moment, last_loud_moment]
end

def find_video_cut_points(movie_filename)
  filename1 = Tempfile.new(['movie-audio-one','.wav'])
  filename2 = Tempfile.new(['movie-audio-two','.wav'])
  system( "ffmpeg -y -i #{movie_filename} -vn -ac 1 -ar 44100 -f wav #{filename1.path} 2>/dev/null" )
  system( "sox #{filename1.path} #{filename2.path}" )
  return find_audio_cut_points(filename2.path)
end

movie_list = []

lines = File.open( ARGV[0] ).readlines
for line in lines
  line = line.gsub( / *#.*/, '' )
  movie_list << line.strip if line.match( /[A-z0-9]/ )
end

cuts = Hash.new

for mts in movie_list
  mp4 = mts.gsub( /\.mts$/, '.mp4' )

  if not mts.match( '-title.mp4' )
    puts "Listening to #{mts}..."
    cuts[mts] = find_video_cut_points( mts )
    puts "  cut in at #{cuts[mts][0]} and out at #{cuts[mts][1]}"
  else
    cuts[mts] = [0,5]
  end
end

#movie_list.collect!{ |x| x.gsub( /\.mts$/, '.mp4' ) }

f = File.open("editlist.xml","w")
f.puts "<mlt>"

for movie in movie_list
  producer = movie.gsub( /\..*/, '' )

  f.puts "  <producer id=\"#{producer}\">"
  f.puts "    <property name=\"resource\">#{movie}</property>"
  f.puts "  </producer>"

  if movie.match( /-flip/ )
f.puts <<EOF
    <tractor id="#{producer}-filtered">
       <multitrack>
         <track producer="#{producer}"/>
       </multitrack>
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
     </tractor>
EOF
  end
end

f.puts <<EOF
  <producer id="theme">
    <property name="resource">music.wav</property>
    <property name="normalise"></property>
  </producer>
EOF

f.puts "  <playlist id=\"main_playlist\">"

for movie in movie_list
  producer = movie.gsub( /\..*/, '' )
  if producer.match( /-flip/ )
    producer = producer + '-filtered'
  end

  cut_in = 0
  cut_out = 30*5

  if not movie.match( '-title.mp4' )
    melted = `melt #{movie} -consumer xml`
    parser = XML::Parser.string(melted)
    doc = parser.parse
    frame_rate_num = doc.find('profile')[0]['frame_rate_num'].to_i
    frame_rate_den = doc.find('profile')[0]['frame_rate_den'].to_i
    frame_rate_num = 90000
    frame_rate_den = 1501
    frame_rate = frame_rate_num.to_f / frame_rate_den.to_f
    frame_rate = 30.0

    cut_in = ((cuts[movie][0] - 0.30) * frame_rate).floor
    cut_out = ((cuts[movie][1] + 0.35) * frame_rate).ceil
  end
  
  f.puts "    <entry producer=\"#{producer}\" in=\"#{cut_in}\" out=\"#{cut_out}\"/>"
end
f.puts "  </playlist>"

f.puts <<EOF
  <playlist id="theme_playlist">
    <entry producer="theme"/>
  </playlist>
  <tractor id="tractor">
    <multitrack>
      <track producer="main_playlist"/>
      <track producer="theme_playlist"/>
    </multitrack>
    <transition id="transition0" out="9999">
      <property name="a_track">0</property>
      <property name="b_track">1</property>
      <property name="mlt_type">transition</property>
      <property name="mlt_service">mix</property>
    </transition>
  </tractor>
EOF

f.puts "</mlt>"
f.close

# http://renomath.org/video/linux/interlace/
