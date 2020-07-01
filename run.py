import click
from selenium.common.exceptions import WebDriverException

from spyders import EGRNSpyder, EGRNStatement


@click.command()
@click.option('--cadnum',
              # prompt='Кадастровый номер',
              help='Кадастровый номер объекта',)
@click.option('--from-file',
              help='Файл со списком кадастровых номеров (каждый номер на новой строке)')


# def collect_data(cadnum, from_file):
#     grabber = EGRNSpyder()

#     if from_file:
#         with open(from_file) as f:
#             for cadnum in f:
#                 print(cadnum)
#                 try:
#                     grabber.save_info(cadnum)
#                 except WebDriverException:
#                     grabber.close()
#                     grabber = EGRNSpyder()
#                     grabber.save_info(cadnum)

#     if cadnum:
#         grabber.save_info(cadnum)

#     grabber.close()



def collect_data(cadnum, from_file):
    grabber = EGRNStatement(task_id='uniq666')
    grabber.get_statement(cadnum)
    # import ipdb; ipdb.set_trace()
    grabber.close()

if __name__ == '__main__':
    collect_data()
