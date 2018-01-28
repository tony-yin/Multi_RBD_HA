from rpyc.utils.classic import connect
import rpyc
import do_shell

def rbd_background(func_name):
    conn = connect('localhost', RBD_PORT)
    module = conn.modules['rbd_utils']
    async_func = rpyc.async(getattr(module, func_name))
    return async_func

@rbd_utils.rbd_background
def remove_image(pool, image):
    while True:
        try:
            logger.info('rbd {} delete start'.format(image))
            do_shell('rbd rm {}/{} >> /var/log/rbd_rm.log'.format(pool, image))
            logger.info('rbd {} delete finish'.format(image))
            break
        except Exception:
            logger.error('rbd {} delete error'.format(image))
            time.sleep(30)
