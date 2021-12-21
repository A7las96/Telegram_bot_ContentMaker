import logging
import sqlite3 as sq

import imagehash

logging.basicConfig(level=logging.INFO)


def ensure_connection(func):
    def inner(*args, **kwargs):
        with sq.connect('photo.db') as conn:
            res = func(*args, conn=conn, **kwargs)
        return res

    return inner


@ensure_connection
def init_db(conn, force: bool = False):
    cur = conn.cursor()
    print('База данных успешно подключена')
    if force:
        cur.execute('DROP TABLE IF EXISTS photo')

    cur.execute('''
     CREATE TABLE IF NOT EXISTS photo(
         file_id TEXT ,
         dHash TEXT PRIMARY KEY,
         pHash TEXT,
         poll_id TEXT)
        '''
                )
    # сохраннение изменений
    conn.commit()


@ensure_connection
async def duplicate_check(state, conn):
    async with state.proxy() as data:

        cur = conn.cursor()

        duplicate_D = False
        duplicate_P = False
        main_duplicate = False
        similar_photos = []
        result = []
        number = 0

        photos_Hash = cur.execute('SELECT dHash, pHash FROM photo').fetchall()

        for i in range(len(photos_Hash)):
            image_dHash = imagehash.hex_to_hash(photos_Hash[i][0])
            image_pHash = imagehash.hex_to_hash(photos_Hash[i][1])
            if imagehash.hex_to_hash(data['d_hash']) - image_dHash < 8:
                duplicate_D = True
                if imagehash.hex_to_hash(data['p_hash']) - image_pHash < 13:
                    duplicate_P = True
                    logging.info('Данное фото уже было')
            elif imagehash.hex_to_hash(data['d_hash']) - image_dHash < 14:
                if imagehash.hex_to_hash(data['p_hash']) - image_pHash < 18:
                    if number < 3:
                        warning = cur.execute('SELECT file_id FROM photo WHERE dHash = ?',
                                              (str(image_dHash),)).fetchone()
                        similar_photos.append(warning[0])
                        number +=1
                        logging.warning('Значительное сходство с некторыми раннее добавленными фото')

        if not (duplicate_D and duplicate_P):
            cur.execute('INSERT INTO photo VALUES (?, ?, ?, ?)', (data['photo'], data['d_hash'], data['p_hash'],''))
            conn.commit()
            logging.info("Фото было добавлено в базу данных")

        main_duplicate = duplicate_D and duplicate_P
        result.append(main_duplicate)
        result.append(similar_photos)
        return result


@ensure_connection
async def poll_id_save(state, conn, id_poll: str = ""):
    async with state.proxy() as data:
        cur = conn.cursor()
        photo_id = data['photo']
        cur.execute('UPDATE photo SET poll_id = ? WHERE file_id = ?', (id_poll, photo_id) )
        conn.commit()
