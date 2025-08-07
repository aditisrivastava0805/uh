#How To Use:
    import sys
    sys.path.insert(0, '/mount/volumes/script/common/lib/process_check/')
    from ProcessCheck import ProcessCheck

    if __name__ == '__main__': 
        pc = ProcessCheck(os.path.join("/", "tmp", os.path.basename(os.path.dirname(os.path.abspath(__file__))) + ".pid"))
        pc.start()
        ....... main code .....
        pc.stop()

