
import time
import requests
from pprint import pprint
import os
from sys import exit
from prometheus_client import start_http_server, Summary
from prometheus_client.core import GaugeMetricFamily, REGISTRY

DEBUG = int(os.environ.get('DEBUG', '0'))

# 计算从emqtt获取metrics总耗时，以及收集的时间戳Summary(metrics,info)
COLLECTION_TIME = Summary('emqtt_collector_collect_seconds', 'Time spent to collect metrics from emqtt')


class EmqttCollector(object):
    # 获取的数据结构
    mqtt_data = {'code': 0,
                 'result': [{'name': 'emqtt@10.244.4.173', 'otp_release': 'R19/8.1', 'memory_total': '157.01M',
                             'memory_used': '112.58M', 'process_available': 2097152, 'process_used': 390,
                             'max_fds': 65536, 'clients': 0, 'node_status': 'Running', 'load1': '3.84',
                             'load5': '2.67', 'load15': '2.24'},
                            {'name': 'emqtt@10.244.5.177', 'otp_release': 'R19/8.1', 'memory_total': '156.44M',
                             'memory_used': '113.39M', 'process_available': 2097152, 'process_used': 394,
                             'max_fds': 65536, 'clients': 2, 'node_status': 'Running', 'load1': '6.51',
                             'load5': '6.15', 'load15': '5.73'},
                            {'name': 'emqtt@10.244.1.169', 'otp_release': 'R19/8.1', 'memory_total': '155.94M',
                             'memory_used': '112.98M', 'process_available': 2097152, 'process_used': 406,
                             'max_fds': 65536, 'clients': 8, 'node_status': 'Running', 'load1': '2.75',
                             'load5': '2.42', 'load15': '1.97'}]}

    def __init__(self, target, user, password):
        self._target = target.rstrip("/")
        self._user = user
        self._password = password

    def collect(self):
        start = time.time()

        # 获取emqtt的job数据
        request_data = self._request_data()
        print(request_data)
        # 制作metrics
        self._setup_empty_prometheus_metrics()

        #传值
        self._add_data_to_prometheus_structure(request_data)  # 为metrics添加值，以及添加labels的值
        for metric in self._prometheus_metrics.values():
            yield metric
        duration = time.time() - start  # 持续的时间
        COLLECTION_TIME.observe(duration)  # 添加jenkins_collector_collect_seconds的值

    # 回去jenkins数据，返回inner函数，函数的值是job
    def _request_data(self):
        # Request exactly the information we need from Jenkins
        url = '{0}/api/v2/monitoring/nodes'.format(self._target)

        def parsejobs(myurl):
            # params = tree: jobs[name,lastBuild[number,timestamp,duration,actions[queuingDurationMillis...
            if self._user and self._password:
                response = requests.get(myurl, auth = (self._user, self._password))
            else:
                response = requests.get(myurl)
            if DEBUG:
                pprint(response.text)
            if response.status_code != requests.codes.ok:
                raise Exception("Call to url %s failed with status: %s" % (myurl, response.status_code))
            result = response.json()
            if DEBUG:
                pprint(result)

            return result

        return parsejobs(url)

    # 制作metric模板，定义labels
    def _setup_empty_prometheus_metrics(self):
        # The metrics we want to export.
        self._prometheus_metrics = {
                'load1':
                    GaugeMetricFamily('emqtt_node_load1',
                                      'emqtt node load1', labels = ["emqtt_node"]),
                'load5':
                GaugeMetricFamily('emqtt_node_load5',
                                  'emqtt node load5', labels = ["emqtt_node"]),
                'memory_used':
                    GaugeMetricFamily('emqtt_node_memory_use',
                                      'emqtt node memory use', labels = ["emqtt_node"]),
                'process_available':
                    GaugeMetricFamily('emqtt_node_process_available',
                                      'emqtt node process available',labels = ["emqtt_node"]),
                'process_used':
                    GaugeMetricFamily('emqtt_node_process_used',
                                      'emqtt node process used',labels = ["emqtt_node"]),
                'max_fds':
                    GaugeMetricFamily('emqtt_node_max_fds',
                                      'emqtt node max fds', labels = ["emqtt_node"]),
                'node_status':
                    GaugeMetricFamily('emqtt_status',
                                      'emqtt status', labels = ["emqtt_node"]),
                'clients':
                    GaugeMetricFamily('emqtt_node_clients',
                                      'emqtt node clients', labels = ["emqtt_node"]),
            }

    # 为每个metric添加值已近添加label的值
    def _add_data_to_prometheus_structure(self,mqtt_data):
        # If there's a null result, we want to pass.
        for emqtt_node_data in mqtt_data['result']:
          name=emqtt_node_data['name']
          for metrics_key in self._prometheus_metrics.keys():
              if 'memory_used' in metrics_key:
                  metrics_value=float(emqtt_node_data[metrics_key].split('M')[0]) * 1024
                  self._prometheus_metrics['memory_used'].add_metric([name],metrics_value)
              elif 'node_status' in metrics_key:
                  if 'Running' in emqtt_node_data['node_status']:
                      self._prometheus_metrics['node_status'].add_metric([name], 1)
                  else:
                      self._prometheus_metrics['node_status'].add_metric([name], 0)
              else:
                  if 'load' in metrics_key:
                      metrics_value=float(emqtt_node_data[metrics_key])
                      self._prometheus_metrics[metrics_key].add_metric([name], metrics_value)
                  else:
                      self._prometheus_metrics[metrics_key].add_metric([name], emqtt_node_data.get(metrics_key))

def main():
    try:
        port = {PORT}
        REGISTRY.register(EmqttCollector('{EMQTT_CLUSTER_URL}', '{EMQTT_AUTH_USER}', '{EMQTT_AUTH_PASS}'))
        start_http_server(port)
        print("http://0.0.0.0:{PORT}")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(" Interrupted")
        exit(0)

if __name__ == "__main__":
    main()