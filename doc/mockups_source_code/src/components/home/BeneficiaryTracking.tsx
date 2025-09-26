import React from 'react';
import { Users, TrendingUp, TrendingDown } from 'lucide-react';

interface BeneficiaryStats {
  totalActive: number;
  newThisMonth: number;
  exitThisMonth: number;
  recentlyHelped: number;
}

const stats: BeneficiaryStats = {
  totalActive: 156,
  newThisMonth: 12,
  exitThisMonth: 4,
  recentlyHelped: 45
};

const BeneficiaryTracking: React.FC = () => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-800">Suivi des Bénéficiaires</h2>
        <Users className="text-purple-600" />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 bg-purple-50 rounded-lg">
          <div className="text-sm text-purple-600 mb-1">Total Actifs</div>
          <div className="text-2xl font-bold text-purple-700">{stats.totalActive}</div>
        </div>
        <div className="p-4 bg-green-50 rounded-lg">
          <div className="flex items-center text-sm text-green-600 mb-1">
            Nouveaux ce mois
            <TrendingUp size={16} className="ml-1" />
          </div>
          <div className="text-2xl font-bold text-green-700">+{stats.newThisMonth}</div>
        </div>
        <div className="p-4 bg-red-50 rounded-lg">
          <div className="flex items-center text-sm text-red-600 mb-1">
            Sorties ce mois
            <TrendingDown size={16} className="ml-1" />
          </div>
          <div className="text-2xl font-bold text-red-700">-{stats.exitThisMonth}</div>
        </div>
        <div className="p-4 bg-blue-50 rounded-lg">
          <div className="text-sm text-blue-600 mb-1">Aidés récemment</div>
          <div className="text-2xl font-bold text-blue-700">{stats.recentlyHelped}</div>
        </div>
      </div>
    </div>
  );
};

export default BeneficiaryTracking;