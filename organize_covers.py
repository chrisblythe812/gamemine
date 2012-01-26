import os


def run(src_path, dst_path):
    item_list = []
    
    files = os.listdir(src_path)
    for f in files:
        p = os.path.join(dst_path, f[:2], f[2:4])
        if not os.path.exists(p):
            os.makedirs(p)
        f_src, f_dst = os.path.join(src_path, f), os.path.join(p, f)
        print '%s --> %s' % (f_src, f_dst)
        os.rename(f_src, f_dst)
        item_list.append('.'.join(f.split('.')[:-1])) 

    with open(os.path.join(dst_path, 'ITEMS'), 'w') as f:
        f.write('\n'.join(item_list)) 


if __name__ == '__main__':
    from sys import argv
    try:
        script, src_path, dst_path = argv
    except:
        print argv
        print 'Please specify source and destination paths'
        exit()
    run(src_path, dst_path)
