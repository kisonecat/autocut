#! /usr/bin/env nix-shell
#! nix-shell -i python3 -p "python3.withPackages(ps: [ps.samplerate ps.numpy ps.matplotlib ps.librosa ps.scipy ps.fastdtw ps.soundfile])"

import xml.etree.ElementTree as ET
import subprocess
import math

def read_fps(video):
  (fps, _w, _h) = read_fps_geom (video)
  return fps

def read_fps_geom(video):
  melted = subprocess.run(["melt", video, "-consumer", "xml"], capture_output=True)
  root = ET.fromstring(melted.stdout)
  frame_rate_num = root.find('profile').get('frame_rate_num')
  frame_rate_den = root.find('profile').get('frame_rate_den')
  fps = float(frame_rate_num) / float(frame_rate_den)
  width = float(root.find('profile').get('width'))
  height = float(root.find('profile').get('height'))
  return (fps,width,height)

def movie2xml(movie):
    videos = movie['videos']

    root = ET.Element('mlt')

    # add producers for video tracks    
    for video in videos:
        # producer for video
        producer = ET.SubElement(root, 'producer')
        source_id =  str(video['id']) + '-source'

        (fps, width, height) = read_fps_geom(video['src'])
        if (width >= height):
          width_crop = int((width - height)/2)
          height_crop = 0
          video_size = int(height/2)
        else:
          height_crop = int((width - height)/2)
          width_crop = 0
          video_size = int(width/2)

        # TODO: get image size from overlay file
        inset_x = 1920 - video_size
        inset_y = 1080 - video_size

        producer.set('id', source_id )
        prop = ET.SubElement(producer, 'property')
        prop.set('name', 'resource')
        prop.text = video['src']

        if 'slide' in video:
          # producer for slide
          producer = ET.SubElement(root, 'producer')
          slide_id =  str(video['id']) + '-slide' 
        
          producer.set('id', slide_id )
          prop = ET.SubElement(producer, 'property')
          prop.set('name', 'resource')
          prop.text = video['slide']

          # the output
          tractor = ET.SubElement(root, 'tractor')
          tractor.set('id', str(video['id']) )

          multitrack = ET.SubElement(tractor, 'multitrack')
          track =  ET.SubElement(multitrack, 'track')
          track.set('producer', source_id )
          track =  ET.SubElement(multitrack, 'track')
          track.set('producer', slide_id )
             
          f = ET.SubElement(tractor, 'transition')
            
          prop = ET.SubElement(f, 'property')
          prop.set('name', 'a_track')
          prop.text = '1'

          prop = ET.SubElement(f, 'property')
          prop.set('name', 'b_track')
          prop.text = '0'          
            
          prop = ET.SubElement(f, 'property')
          prop.set('name', 'mlt_type')
          prop.text = 'transition'            

          prop = ET.SubElement(f, 'property')
          prop.set('name', 'mlt_service')
          prop.text = 'frei0r.cairoblend'

          prop = ET.SubElement(f, 'property')
          prop.set('name', '1')
          prop.text = 'add'
        elif 'overlay' in video:
          # producer for slide
          producer = ET.SubElement(root, 'producer')
          slide_id =  str(video['id']) + '-overlay' 
        
          producer.set('id', slide_id )
          prop = ET.SubElement(producer, 'property')
          prop.set('name', 'resource')
          prop.text = video['overlay']

          # producer for CROPPED video
          tractor = ET.SubElement(root, 'tractor')
          cropped_id =  str(video['id']) + '-cropped' 
          tractor.set('id', cropped_id )

          multitrack = ET.SubElement(tractor, 'multitrack')
          track =  ET.SubElement(multitrack, 'track')
          track.set('producer', source_id )

          f = ET.SubElement(tractor, 'filter')
            
          prop = ET.SubElement(f, 'property')
          prop.set('name', 'track')
          prop.text = '0'

          prop = ET.SubElement(f, 'property')
          prop.set('name', 'mlt_service')
          prop.text = 'crop'

          prop = ET.SubElement(f, 'property')
          prop.set('name', 'left')
          prop.text = '{:d}'.format(width_crop)

          prop = ET.SubElement(f, 'property')
          prop.set('name', 'right')
          prop.text = '{:d}'.format(width_crop)

          prop = ET.SubElement(f, 'property')
          prop.set('name', 'top')
          prop.text = '{:d}'.format(height_crop)

          prop = ET.SubElement(f, 'property')
          prop.set('name', 'bottom')
          prop.text = '{:d}'.format(height_crop)

          f = ET.SubElement(tractor, 'filter')
            
          prop = ET.SubElement(f, 'property')
          prop.set('name', 'track')
          prop.text = '0'
            
          prop = ET.SubElement(f, 'property')
          prop.set('name', 'mlt_service')
          prop.text = 'affine'

          prop = ET.SubElement(f, 'property')
          prop.set('name', 'transition.rect')
          prop.text = '{x:d}/{y:d}:{size:d}x{size:d}'.format(x=inset_x, y=inset_y, size=video_size)


          # the output
          tractor = ET.SubElement(root, 'tractor')
          tractor.set('id', str(video['id']) )

          multitrack = ET.SubElement(tractor, 'multitrack')
          track =  ET.SubElement(multitrack, 'track')
          track.set('producer', cropped_id )
          track =  ET.SubElement(multitrack, 'track')
          track.set('producer', slide_id )

             
          f = ET.SubElement(tractor, 'transition')
            
          prop = ET.SubElement(f, 'property')
          prop.set('name', 'a_track')
          prop.text = '1'

          prop = ET.SubElement(f, 'property')
          prop.set('name', 'b_track')
          prop.text = '0'          
            
          prop = ET.SubElement(f, 'property')
          prop.set('name', 'mlt_type')
          prop.text = 'transition'            

          prop = ET.SubElement(f, 'property')
          prop.set('name', 'mlt_service')
          prop.text = 'frei0r.cairoblend'

          prop = ET.SubElement(f, 'property')
          prop.set('name', '1')
          prop.text = 'add'

        else:
        
          tractor = ET.SubElement(root, 'tractor')
          tractor.set('id', str(video['id']) )

          multitrack = ET.SubElement(tractor, 'multitrack')
          track =  ET.SubElement(multitrack, 'track')
          track.set('producer', source_id )

          if 'flip' in video:
            f = ET.SubElement(tractor, 'filter')
            
            prop = ET.SubElement(f, 'property')
            prop.set('name', 'track')
            prop.text = '0'
            
            prop = ET.SubElement(f, 'property')
            prop.set('name', 'mirror')
            prop.text = 'flip'            

            prop = ET.SubElement(f, 'property')
            prop.set('name', 'mlt_service')
            prop.text = 'mirror'            

            f = ET.SubElement(tractor, 'filter')
            
            prop = ET.SubElement(f, 'property')
            prop.set('name', 'track')
            prop.text = '0'
            
            prop = ET.SubElement(f, 'property')
            prop.set('name', 'mirror')
            prop.text = 'flop'            

            prop = ET.SubElement(f, 'property')
            prop.set('name', 'mlt_service')
            prop.text = 'mirror'            

    # add producers for extra audio tracks            
    for video in videos:
        if 'audio' in video:
            producer = ET.SubElement(root, 'producer')
            producer.set('id', str(video['id']) + '-audio' )

            prop = ET.SubElement(producer, 'property')
            prop.set('name', 'resource')
            prop.text = video['audio']
            
            prop = ET.SubElement(producer, 'property')
            prop.set('name', 'normalise')

    # write main playlist, storing starting frames along the way
    playlist_id = "main-playlist"
    playlist = ET.SubElement(root, 'playlist')
    playlist.set('id', playlist_id)
    
    scene_start = 0
    for video in videos:
        fps = read_fps(video['src'])
        cut_in = math.floor(float(video['in']) * fps)
        cut_out = math.ceil(float(video['out']) * fps)
        
        video['start'] = scene_start
        scene_length = cut_out - cut_in
        scene_start = scene_start + scene_length

        entry = ET.SubElement(playlist, 'entry')
        entry.set('producer', str(video['id']) )
        entry.set('in', str(cut_in) )
        entry.set('out', str(cut_out) )

    total_frames = scene_start        

    # make playlists to mix together the extra audio tracks

    for video in videos:
        if 'audio' in video:
            playlist = ET.SubElement(root, 'playlist')
            playlist.set('id', str(video['id']) + '-audio-playlist' )
            blank = ET.SubElement(playlist, 'blank')
            blank.set('length', str(video['start']) )

            entry = ET.SubElement(playlist, 'entry')
            entry.set('producer', str(video['id']) + '-audio' )
            entry.set('out', str(total_frames - video['start']) )

            tractor = ET.SubElement(root, 'tractor')
            tractor.set('id', playlist_id + '-mix' )

            multitrack = ET.SubElement(tractor, 'multitrack')
            
            track = ET.SubElement(multitrack, 'track')
            track.set('producer', playlist_id )

            track = ET.SubElement(multitrack, 'track')
            track.set('producer', str(video['id']) + '-audio-playlist' )

            transition = ET.SubElement(tractor, 'transition')
            transition.set('id', 'transition-' + playlist_id )
            transition.set('out', str(total_frames) )

            prop = ET.SubElement(transition, 'property')
            prop.set('name', 'a_track')
            prop.text = '0'

            prop = ET.SubElement(transition, 'property')
            prop.set('name', 'b_track')
            prop.text = '1'            

            prop = ET.SubElement(transition, 'property')
            prop.set('name', 'mlt_type')
            prop.text = 'transition'            

            prop = ET.SubElement(transition, 'property')
            prop.set('name', 'mlt_service')
            prop.text = 'mix'            

            playlist_id = playlist_id + '-mix'


    tree = ET.ElementTree()
    tree._setroot(root)
    return tree

