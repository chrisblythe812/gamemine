
ATTR_SCREENSHOT = 'GA0000002872'
ATTRS_CLIP = [
    'GA0000002861', # Trailer 
    'GA0000002859', # MovieClip
    'GA0000002857', # GameplaySampleSingleplayer 
    'GA0000002858', # GameplaySampleMultiplayer
    'GA0000002864', # Preview 
    'GA0000002862', # Commercial 
    'GA0000002856', # Cinematic 
    'GA0000002870', # BehindTheScenes
]


class Muze():
    def __init__(self, connection):
        self.connection = connection
        
    
    def _get_cursor(self):
        return self.connection.cursor()
        
        
    def get_work_id(self, upc):
        cursor = self._get_cursor()
        cursor.execute('SELECT WorkId FROM Release WHERE UPC = %s;', (upc, ))
        row = cursor.fetchone() or [None]
        return row[0]


    def get_screenshots(self, work_id):
        if not work_id:
            return []
        cursor = self._get_cursor()
        cursor.execute('''
        SELECT 
            p_FileName,
            Caption 
         FROM ImageLink WHERE MainObjectID = %s AND ClassificationAttributeID=%s;''', 
                       (work_id, ATTR_SCREENSHOT))
        res = []
        for r in cursor:
            res.append({
                'file_name': r[0].replace('\\', '/'),
                'caption': r[1],
            })
        return res
    
    def get_videos(self, work_id):
        if not work_id:
            return []
        cursor = self._get_cursor()
        fields = ', '.join(['%s'] * len(ATTRS_CLIP))
        aaa = [work_id] + ATTRS_CLIP
        cursor.execute('''
        SELECT 
            p_filename,
            caption
        FROM ClipLink WHERE MainObjectID = %s AND ClassificationAttributeID in (''' + fields + ''');''', 
                       aaa)
        res = []
        for r in cursor:
            res.append({
                'file_name': r[0].replace('\\', '/'),
                'caption': r[1],
            })
        return res
    
    def get_videos2(self, work_id):
        if not work_id:
            return []
        cursor = self._get_cursor()
        cursor.execute('''
            select
                (select C.Caption
                    from cliplink C
                    where C.p_setid = A.p_setid
                        and coalesce(C.Caption, '') <> ''
                        and C.mainobjectid = A.mainobjectid
                    limit 1) Caption,
                (select FH.p_filename
                    from cliplink FH
                    where FH.p_setid = A.p_setid
                        and FH.p_mimetype = 'video/x-flv'
                        and FH.mainobjectid = A.mainobjectid
                    order by FH.p_width desc, FH.p_height desc
                    limit 1) flv_high,
                (select FL.p_filename
                    from cliplink FL
                    where FL.p_setid = A.p_setid
                        and FL.p_mimetype = 'video/x-flv'
                        and FL.mainobjectid = A.mainobjectid
                    order by FL.p_width asc, FL.p_height asc
                    limit 1) flv_low,
                (select QH.p_filename
                    from cliplink QH
                    where QH.p_setid = A.p_setid
                        and QH.p_mimetype = 'video/quicktime'
                        and QH.mainobjectid = A.mainobjectid
                    order by QH.p_width desc, QH.p_height desc
                    limit 1) qt_high,
                (select QL.p_filename
                    from cliplink QL
                    where QL.p_setid = A.p_setid
                        and QL.p_mimetype = 'video/quicktime'
                        and QL.mainobjectid = A.mainobjectid
                    order by QL.p_width desc, QL.p_height desc
                    limit 1) qt_low
            
            from cliplink A
            where A.mainobjectid = %s
            group by A.mainobjectid, A.p_setid
        ''', (work_id, ))
        res = []
        for r in cursor:
            record = {
                'caption': r[0],
                'f1': (r[1] or '').replace('\\', '/'),
                'f2': (r[2] or '').replace('\\', '/'),
                'f3': (r[3] or '').replace('\\', '/'),
                'f4': (r[4] or '').replace('\\', '/'),
            }
            if record['f1'] or record['f2']:
                res.append(record)
        return res
    
    
    def get_front_image(self, work_id):
        if not work_id:
            return None
        cursor = self._get_cursor()
        cursor.execute('''
        SELECT 
            p_FileName
        FROM ImageLink WHERE MainObjectID = %s AND ClassificationAttributeID=%s
        ORDER BY p_Width DESC;''', 
                       (work_id, ''))
        for r in cursor:
            return r[0].replace('\\', '/')
        return None
    
    
    def get_expanded_description(self, work_id):
        if not work_id:
            return None
        
        cursor = self._get_cursor()
        cursor.execute('''
        SELECT
            Value
        FROM
            AttributeLink WHERE ObjectID = %s AND PropertyAttributeID = %s;''',
                        (work_id, 'GA0000000244'))
        for r in cursor:
            return r[0]
        return None

    def get_msrp(self, work_id):
        if not work_id:
            return None
        
        cursor = self._get_cursor()
        cursor.execute("""
        SELECT
            Msrp
        FROM
            Release WHERE WorkID = %s and Territory = 'US';""",
                        (work_id, ))
        for r in cursor:
            return r[0]
        return None
        