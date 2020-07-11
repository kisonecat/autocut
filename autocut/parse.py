import xml.etree.ElementTree as ET
from autocut.listen import listen_for_start_and_end

def parse_input(filename):
    tree = ET.parse(filename)
    root = tree.getroot()

    if root.tag != 'movie':
        raise Exception('the root tag must be <movie>')

    author = root.get('author')
    title = root.get('title')

    videos = []
    index = 1

    for child in root:
        if child.tag != 'video':
            raise Exception('the child tags must be <video>')
    
        attributes = child.attrib
    
        if not 'src' in attributes:
            raise Exception('missing src attribute on video ' + str(index))
        src = attributes['src']
        if not ('in' in attributes and 'out' in attributes):
            print("Listening to",src)
            starting, ending = listen_for_start_and_end(src)
            if not 'in' in attributes:
                attributes['in'] = starting
            if not 'out' in attributes:
                attributes['out'] = ending
                
        attributes['id'] = index
        
        videos.append( attributes )
        
        index = index + 1

    return { 'author': author,
             'title': title,
             'videos': videos }

