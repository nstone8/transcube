import sys
import pandas as pd
import itertools

en=[
    [0x0041,0x005A],
    [0x0061,0x007A]
]
jap=[
    [0x3040,0x309F],
    [0x30A0,0x30FF],
    [0x4E00,0x9FFF]
]

def get_num_contiguous_bmp_characters(test_str):
    #print('get contiguous')
    count=0
    if not count<len(test_str):
        return count
    while (ord(test_str[count]) > 0x1F) and (ord(test_str[count])<=0xFFFF):
        count+=1
        if not count<len(test_str):
            break
    return count

def get_ratio_in_lang(test_str,lang):
    #print('get ratio')
    count_in=0
    for a in test_str:
        this_ord=ord(a)
        for span in lang:
            if this_ord>=span[0] and this_ord<=span[1]:
                count_in+=1
                break
    return count_in/len(test_str)

def rip(rom_file,min_char=3,max_char=500,lang=en+jap,ratio_lang=.75,cur_start=0):
    print(f'ripping {rom_file}')
    print('Looking for text')
    rom=open(rom_file,'rb').read()

    len_rom=len(rom)
    cur=cur_start
    strings=[]
    start_index=[]
    stop_index=[]
    while cur<len_rom:
        #print(f'outer, cur={cur}')
        #print(f'{100*cur/len_rom}%')
        if not cur%1E6:
            percent_complete=format(100*(cur/len_rom),'.3')
            print('\r'+' '*50,end='')
            print(f'\r{percent_complete}% complete',end='')

        if not cur%1E8:
            print('\t Removing Duplicates',end='')
            strings,start_index,stop_index=remove_duplicates(strings,start_index,stop_index)

        old_cur=cur
        this_chunk=[]
        if len_rom-cur<4:
            this_chunk=rom[cur:]
            cur=len_rom
        else:
            this_chunk=rom[cur:cur+4]
            cur+=4

        #Try to convert our chunk to unicode

        try:
            this_chunk_str=this_chunk.decode()

        except(UnicodeDecodeError):
            #move on

            cur=old_cur+1
            continue

        #see if we have any good characters at the beginning of our string
        if not get_num_contiguous_bmp_characters(this_chunk_str):
            cur=old_cur+1
            continue

        #now see how many we can get

        old_len=0
        while (get_num_contiguous_bmp_characters(this_chunk_str)>old_len) and ((len_rom-cur)>4):
            #print(f'inner, cur={cur}')
            #print(f'{100*cur/len_rom}%')
            old_len=get_num_contiguous_bmp_characters(this_chunk_str)
            if old_len>max_char:
                break
            this_chunk+=rom[cur:cur+4]
            #need to add check for EOF
            cur+=4
            try:
                this_chunk_str=this_chunk.decode()

            except(UnicodeDecodeError):
                #move on
                break

        this_chunk_str_trunc=this_chunk_str[:get_num_contiguous_bmp_characters(this_chunk_str)]
        if (len(this_chunk_str_trunc))>min_char and (get_ratio_in_lang(this_chunk_str_trunc,lang)>=ratio_lang):
            strings.append(this_chunk_str_trunc)
            #print(strings[-1])
            start_index.append(old_cur)
            stop_index.append(old_cur+len(this_chunk_str_trunc.encode()))
            #print(100*cur/len_rom)

        cur=old_cur+1
    print('')
    out=remove_duplicates(strings,start_index,stop_index)
    return make_df(*out)

'''def remove_duplicates(strings,start_index,stop_index):
    word_frame=pd.DataFrame(dict(phrase=strings,start_index=start_index,stop_index=stop_index,unique=True))
    indices=list(range(word_frame.shape[0]))
    indices.reverse()
    for i in indices:
        #print(i)
        if not word_frame.loc[i,:]['unique']:
            continue
        this_start=word_frame.iloc[i,:]['start_index']
        this_end=word_frame.iloc[i,:]['stop_index']
        start_greater=word_frame['start_index']<=this_start
        end_less=word_frame['stop_index']>this_end
        inside_me=start_greater & end_less
        word_frame.loc[inside_me,'unique']=False'''

'''def remove_duplicates(strings,start_index,stop_index):
    #print('remove duplicates')
    word_frame=pd.DataFrame(dict(phrase=strings,start_index=start_index,stop_index=stop_index,unique=True))
    indices=list(range(word_frame.shape[0]))
    #indices.reverse()
    for i in indices:
        if not i%1000:
            print(f'{i}/{word_frame.shape[0]}')
        if not word_frame.loc[i,:]['unique']:
            continue
        this_start=word_frame.iloc[i,:]['start_index']
        this_end=word_frame.iloc[i,:]['stop_index']
        j=1
        if (i+j)>=word_frame.shape[0]:
            continue
        while word_frame.loc[i+j,'stop_index']<=this_end:
            print(f'j={j}')
            if word_frame.loc[i+j,'start_index']>=this_start:
                word_frame.loc[i+j,'unique']=False
            j+=1
            if (i+j)>=word_frame.shape[0]:
                break
    word_frame=word_frame.loc[word_frame.loc[:,'unique'],:]
    return word_frame,list(word_frame['phrase']),list(word_frame['start_index']),list(word_frame['stop_index'])'''

def remove_duplicates(strings,start_index,stop_index):
    #print('remove duplicates')
    if not strings:
        return [],[],[]
    strings_out=[]
    start_index_out=[]
    stop_index_out=[]
    ziploc=zip(strings,start_index,stop_index)
    old_string,old_start,old_stop=next(ziploc)

    strings_out.append(old_string)
    start_index_out.append(old_start)
    stop_index_out.append(old_stop)

    for new_string, new_start, new_stop in ziploc:
        if not (new_string in old_string):
            strings_out.append(new_string)
            start_index_out.append(new_start)
            stop_index_out.append(new_stop)
        old_string=new_string
        old_start=new_start
        old_stop=new_stop

    return strings_out,start_index_out,stop_index_out

def make_df(strings,start_index,stop_index):
    return pd.DataFrame(dict(phrase=strings,start_index=start_index,stop_index=stop_index))

def decompose_df(df):
    strings=list(df['phrase'])
    start=list(df['start_index'])
    end=list(df['stop_index'])
    return strings,start,end

def filter_by_substring(strings,start_index,stop_index,bad_words):
    good_lines=[]
    for bad in bad_words:
        print(bad)
        good_lines.append([not (bad in a) for a in strings])
    if len(bad_words)>1:
        naughty_list=[all(x) for x in zip(good_lines)]
    else:
        naughty_list=good_lines[0]
    #print(list(zip(good_lines)))
    return list(itertools.compress(strings,naughty_list)),list(itertools.compress(start_index,naughty_list)),list(itertools.compress(stop_index,naughty_list))

def search_by_substring(strings,start_index,stop_index,search):
    good_lines=[search in a for a in strings]
    #print(list(zip(good_lines)))
    return list(itertools.compress(strings,good_lines)),list(itertools.compress(start_index,good_lines)),list(itertools.compress(stop_index,good_lines))

def replace_text(rom_in,rom_out,replacement_frame):
    print('Loading ROM')
    with open(rom_in,'rb') as ri:
        rom_bytes=bytearray(ri.read())
    replacement_frame=replacement_frame.dropna()
    print('Replacing')
    for i in range(replacement_frame.shape[0]):
        this_row=replacement_frame.iloc[i,:]
        if rom_bytes[this_row['start_index']:this_row['stop_index']].decode()==this_row['phrase']:
            #Everything looks good, check that replacement will fit
            diff_len_bytes=len(this_row['phrase'].encode())-len(this_row['Replacement'].encode())
            if diff_len_bytes<0:
                print(f'Replacement on line {i} will not fit in corresponding space. Skipping')
                continue
            replacement_padded=this_row['Replacement']+' '*diff_len_bytes
            rom_bytes[this_row['start_index']:this_row['stop_index']]=replacement_padded.encode()
        else:
            print(f'Replacement on line {i} does not match original phrase. Maybe this location has been edited by another replacement. Skipping')
            continue

    print('Saving ROM')
    with open(rom_out,'wb') as ro:
        ro.write(rom_bytes)
