from api.view import BaseView, route, menu

import netfilter


class FirewallView(BaseView):
    @menu('Overview', icon='fire-extinguisher', order=0)
    def overview(self):
        try:
            from netfilter.table import Table
            table = Table('raw')
            print(table.list_chains())
        except netfilter.table.IptablesError as e:
            return ('error', {
                                'title': 'IPTables', 'error': 'Unable to initialize IPTables. Do you need to insmod?',
								'fixes': [
									{
										'text': 'IPTables must be inserted as a module into the linux kernel.',
										'command': 'modprobe ip_tables'
									}, {
										'text': 'Update your installed packages.',
										'command': 'yum -y update'
									}, {
										'text': 'Update your kernel. Then, restart your system.',
										'command': 'yum -y update kernel'
									}
								]
                            }
						)
        return ('overview.html')
