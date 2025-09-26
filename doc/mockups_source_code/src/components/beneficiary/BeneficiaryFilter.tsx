import React from 'react';
import { Search } from 'lucide-react';

interface FilterProps {
  filters: {
    search: string;
    status: string;
  };
  onFilterChange: (filters: any) => void;
}

const BeneficiaryFilter: React.FC<FilterProps> = ({ filters, onFilterChange }) => {
  return (
    <div className="bg-white p-4 rounded-lg shadow-sm mb-6">
      <div className="flex gap-4 items-center">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            placeholder="Rechercher un bénéficiaire..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            value={filters.search}
            onChange={(e) => onFilterChange({ ...filters, search: e.target.value })}
          />
        </div>
        <select
          className="border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          value={filters.status}
          onChange={(e) => onFilterChange({ ...filters, status: e.target.value })}
        >
          <option value="all">Tous les statuts</option>
          <option value="active">Actif</option>
          <option value="inactive">Inactif</option>
        </select>
      </div>
    </div>
  );
};

export default BeneficiaryFilter;