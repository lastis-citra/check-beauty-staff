import requests
from bs4 import BeautifulSoup


def display_result_table(result_table, day_list, time_list, staff_name_list):
    column_i = 0
    for result_row in result_table:
        print(day_list[column_i])
        row_i = 0
        for result_cell in result_row:
            staff = ''
            print(time_list[row_i], end=' ')
            if result_cell is None:
                result_text = 'n'
                print(result_text, end='')
            else:
                cell_i = 0
                for result in result_cell:
                    if result:
                        result_text = 'o'
                        if staff_name_list[cell_i] is None:
                            if staff == '':
                                staff += 'WARNING!'
                            else:
                                staff += 'OK!'
                        else:
                            staff += staff_name_list[cell_i] + ','
                    else:
                        result_text = 'x'
                    print(result_text, end=' ')
                    cell_i += 1
                print(staff, end='')
            print('')
            row_i += 1
        print('\n')
        column_i += 1


def get_day_list(th_tags, debug):
    day_list = []

    for th_tag in th_tags:
        day = th_tag.text.replace('\t', '').split('\n')[1]
        if debug:
            print(day)
        day_list.append(day)

    return day_list


def get_time_list(th_tags, debug):
    time_list = []

    for th_tag in th_tags:
        if debug:
            print(th_tag.text)
        time_list.append(th_tag.text)

    return time_list


def init_result_table(max_col, max_row, debug):
    if debug:
        print(f'max_col: {max_col}, max_row: {max_row}')

    result_table = []
    for column_i in range(max_col):
        result_table_row = []
        for row_i in range(max_row):
            result_table_row.append([])
        result_table.append(result_table_row)

    return result_table


def check_staff_schedule(session, store_id, coupon_id, staff_list, debug):
    result_table = []
    staff_name_list = []
    day_list = []
    time_list = []

    staff_i = 0
    for staff in staff_list:
        if staff[0] is None:
            staff_url = f'https://beauty.hotpepper.jp/CSP/kr/reserve/salonSchedule?storeId={store_id}'
            staff_name_list.append(None)
        else:
            staff_url = f'https://beauty.hotpepper.jp/CSP/kr/reserve/schedule?storeId={store_id}&couponId={coupon_id}' \
                        f'&add=0&staffId={staff[0]}'
            staff_name_list.append(staff[1])

        res = session.get(staff_url)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, 'html.parser')

        # 日付リスト取得
        if staff[0] is not None and len(day_list) == 0:
            th_tags = soup.select('.dayCellContainer th')
            day_list = get_day_list(th_tags, debug)

        # 時刻リスト取得
        if staff[0] is not None and len(time_list) == 0:
            th_tags = soup.select('.moreInnerTable.timeTableLeft tr th')
            time_list = get_time_list(th_tags, debug)

        # 表の日数（何日分の列があるか，通常14日分）
        table_tags = soup.select('table[class=moreInnerTable]')
        column_i = 0

        table_tags_num = len(table_tags)
        if debug:
            print(f'table_tags_num: {table_tags_num}')

        for table_tags_c in range(table_tags_num):
            row_i = 0
            # 各列に何個分の◎✕があるか
            td_tags = soup.select('table[class=moreInnerTable]')[table_tags_c].select('tr td')

            if debug:
                print(f'td_tags_num: {len(list(td_tags))}')

            if staff_i == 0 and column_i == 0 and row_i == 0:
                result_table = init_result_table(table_tags_num, len(list(td_tags)), debug)

            result_row = result_table[column_i]

            for td_tag in td_tags:
                if debug:
                    print(f'staff: {staff_i}, col: {column_i}, row: {row_i}')
                result_bool = None

                if '×' in td_tag.text:
                    result_bool = False
                    if debug:
                        print('x')
                elif '◎' in td_tag.text:
                    result_bool = True
                    if debug:
                        print('o')

                result_cell = result_row[row_i]
                if len(result_cell) == 0:
                    result_cell = [result_bool]
                else:
                    result_cell.append(result_bool)

                result_row[row_i] = result_cell
                row_i += 1

            result_table[column_i] = result_row
            column_i += 1
        staff_i += 1

    return result_table, day_list, time_list, staff_name_list


def get_staffs(session, store_id, debug):
    staffs_url = f'https://beauty.hotpepper.jp/CSP/kr/reserve/scheduledStaff?storeId={store_id}'
    res = session.get(staffs_url)
    # res.encoding = res.apparent_encoding
    # soup = BeautifulSoup(res.text, 'html.parser')
    soup = BeautifulSoup(res.content, 'html.parser')

    staff_id_list = []
    a_tags = soup.select('.bdGrayR.w148 div div a')
    for a_tag in a_tags:
        staff_id = a_tag['class'][1].split('_')[1]
        if debug:
            print(staff_id)
        staff_id_list.append(staff_id)
    # 最後に全体のスケジュールと照合するため
    staff_id_list.append(None)

    staff_name_list = []
    p_tags = soup.select('.bdGrayR.w148 div .mT5')
    for p_tag in p_tags:
        staff_name = p_tag.text.split(' ')[0]
        if debug:
            print(staff_name)
        staff_name_list.append(staff_name)
    # 最後に全体のスケジュールと照合するため
    staff_name_list.append(None)

    return list(zip(staff_id_list, staff_name_list))


def create_session(store_id, coupon_id):
    top_url = 'https://beauty.hotpepper.jp/kr/sln' + store_id
    reserve_url = 'https://beauty.hotpepper.jp/CSP/kr/reserve/?storeId=' + store_id
    coupon_url = 'https://beauty.hotpepper.jp/CSP/kr/reserve/afterCoupon?storeId=' + store_id + '&couponId=' \
                 + coupon_id + '&add=0'

    session = requests.Session()
    session.get(top_url)
    session.get(reserve_url)
    session.get(coupon_url)
    return session


if __name__ == '__main__':
    DEBUG = False
    # _store_id = 'H000471245'
    # _coupon_id = 'CP00000005985046'  # 60分

    _store_id = 'H000584797'
    _coupon_id = 'CP00000007682902'  # 80分+10分

    _session = create_session(_store_id, _coupon_id)
    _staff_list = get_staffs(_session, _store_id, DEBUG)
    _result_table, _day_list, _time_list, _staff_name_list = check_staff_schedule(_session, _store_id, _coupon_id,
                                                                                  _staff_list, DEBUG)
    display_result_table(_result_table, _day_list, _time_list, _staff_name_list)
