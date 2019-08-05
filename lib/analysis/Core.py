from pathlib import Path

from datetime import datetime
from sqlalchemy.orm import sessionmaker

from lib.adb import Device
from lib.model import Application, Url
from lib.model.Analysis import Analysis
from lib.model.database.Database import Database
from lib.receiver.Frida import Frida
from lib.receiver.Proxy import Proxy

import logging
import time
import uuid
import sys

from lib.report.ReportGenerator import ReportGenerator


class Core:

    def __init__(self, configuration, device: Device, module, path: str):
        self.configuration = configuration
        self.device = device
        self.path = path
        self.module = module
        self.session = None
        self.timeout = int(configuration['ANALYSIS'].get('analysis_timeout'))


        # Object used by the core
        self.current_application = None
        self.receivers = []

        # Database initialisation
        session = Database.get_session()
        self.analysis = Analysis(uuid=str(uuid.uuid4()), date=datetime.now())
        session.add(self.analysis)
        session.commit()

    def select_applications(self):
        '''
        Return the applications that will be analyzed
        :return:
        '''
        logging.debug("Core:select_applications()")
        return self.module.select(self.path, )

    def start_analysis(self):
        '''
        Launch the analysis process and loop trough all apk
        then generate the according report
        :return:
        '''
        logging.debug("Core:start_analysis()")

        apk_paths = self.select_applications()
        print(apk_paths)
        if self.configuration['ANALYSIS'].getboolean('use_proxy'):
            self.device.install_certificate(self.configuration['PROXY'].get('proxy_certificate'))

        if self.configuration['ANALYSIS'].getboolean('use_frida'):
            Frida.compile(configuration=self.configuration)
            self.device.install_frida()

        for apk in apk_paths:
            self.analyse_sample(Path(apk).absolute())

        # Rapport generating
        generator = ReportGenerator()
        report_path = generator.generate(self.analysis)
        path = str(Path(report_path).absolute())
        logging.info(f"Report generated to {path}")

    def analyse_sample(self, apk_path):
        '''
        Analyze the given apk
        :param apk_path:
        :return:
        '''
        logging.debug("Core:analyse_sample()")

        self.current_application = Application.Application(apk_path)

        # Database storing
        session = Database.get_session()
        self.analysis.application.append(self.current_application)
        session.add(self.current_application)
        session.commit()

        logging.info(f"Package name: {self.current_application.package}")
        logging.info(f"Main activity: {self.current_application.get_main_activity()}")
        logging.info(f"Path : {self.current_application.path}")
        logging.info(f"SHA256 : {self.current_application.get_sha256_hash()}")

        time_init = time.time()

        module = self.module(self.current_application)

        self.device.uninstall_application(self.current_application.package)
        self.device.install_application(self.current_application.path)
        self.start_receivers(module)

        current_time = 0
        while current_time < self.timeout or ( self.timeout == -1 and self.device.check_is_up() ) :
            current_time = time.time() - time_init
            logging.debug(current_time)
            time.sleep(1)

        self.stop_receivers()
        if(self.timeout!= -1):
            self.device.uninstall_application(self.current_application.package)

    def start_receivers(self, module):
        '''
        Start handler that handles the devices interactions
        :param module:
        :return:
        '''
        logging.debug("Core:start_receivers()")

        use_frida = self.configuration['ANALYSIS'].getboolean('use_frida')
        use_proxy = self.configuration['ANALYSIS'].getboolean('use_proxy')

        if use_proxy:
            proxy = Proxy(self.configuration['PROXY'], module)
            proxy.start()
            self.receivers.append(proxy)

        if use_frida:
            frida = Frida(self.configuration['FRIDA'], module, self.device)
            frida.start()
            self.receivers.append(frida)
        else:
            self.device.launch_application(self.current_application.package)

        logging.debug("Core:start_receivers() -> Started")

    def stop_receivers(self):
        '''
        Stop all current handlers
        :return:
        '''
        logging.debug("Core:stop_receivers()")

        for i in range(len(self.receivers)):
            self.receivers[i].stop()

        self.receivers = []
