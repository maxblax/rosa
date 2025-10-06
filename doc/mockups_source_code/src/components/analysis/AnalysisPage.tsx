import React from 'react';
import { Download } from 'lucide-react';
import DisposableIncomeChart from './charts/DisposableIncomeChart';
import BeneficiaryCountChart from './charts/BeneficiaryCountChart';
import InteractionCountChart from './charts/InteractionCountChart';
import PartnerDeliveriesChart from './charts/PartnerDeliveriesChart';
import donationsChart from './charts/donationsChart';
import NewBeneficiariesChart from './charts/NewBeneficiariesChart';
import FollowUpDurationChart from './charts/FollowUpDurationChart';

const AnalysisPage: React.FC = () => {
  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Analyses</h1>
        <button className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2">
          <Download size={20} />
          Exporter les données
        </button>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <DisposableIncomeChart />
        <BeneficiaryCountChart />
        <InteractionCountChart />
        <PartnerDeliveriesChart />
        <donationsChart />
        <NewBeneficiariesChart />
        <FollowUpDurationChart className="col-span-2" />
      </div>
    </div>
  );
};

export default AnalysisPage;