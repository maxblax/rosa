import React, { useState } from 'react';
import { ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface Beneficiary {
  id: number;
  email: string;
  lastName: string;
  firstName: string;
  civility: string;
  birthDate: string;
  phone: string;
  tags: string[];
  lastInteraction: string;
}

const mockData: Beneficiary[] = [
  {
    id: 1,
    email: 'jean.dupont@email.com',
    lastName: 'Dupont',
    firstName: 'Jean',
    civility: 'M.',
    birthDate: '1985-06-15',
    phone: '06 12 34 56 78',
    tags: ['Urgent', 'Médical'],
    lastInteraction: '2024-03-15'
  },
  {
    id: 2,
    email: 'marie.martin@email.com',
    lastName: 'Martin',
    firstName: 'Marie',
    civility: 'Mme',
    birthDate: '1990-03-22',
    phone: '06 98 76 54 32',
    tags: ['Alimentaire'],
    lastInteraction: '2024-03-18'
  }
];

interface TableProps {
  filters: {
    search: string;
    status: string;
  };
}

const BeneficiaryTable: React.FC<TableProps> = ({ filters }) => {
  const navigate = useNavigate();
  const [selectedRows, setSelectedRows] = useState<number[]>([]);
  const [sortField, setSortField] = useState<keyof Beneficiary>('lastName');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      setSelectedRows(mockData.map(b => b.id));
    } else {
      setSelectedRows([]);
    }
  };

  const handleSelectRow = (id: number) => {
    if (selectedRows.includes(id)) {
      setSelectedRows(selectedRows.filter(rowId => rowId !== id));
    } else {
      setSelectedRows([...selectedRows, id]);
    }
  };

  const handleSort = (field: keyof Beneficiary) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const SortIcon = ({ field }: { field: keyof Beneficiary }) => {
    if (sortField !== field) return null;
    return sortDirection === 'asc' ? <ChevronUp size={16} /> : <ChevronDown size={16} />;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left">
                <input
                  type="checkbox"
                  checked={selectedRows.length === mockData.length}
                  onChange={handleSelectAll}
                  className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                ID
              </th>
              {['Email', 'Nom', 'Prénom', 'Civilité', 'Date de naissance', 'Téléphone', 'Étiquettes', 'Dernière interaction'].map((header, index) => (
                <th
                  key={header}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                  onClick={() => handleSort(Object.keys(mockData[0])[index + 1] as keyof Beneficiary)}
                >
                  <div className="flex items-center gap-1">
                    {header}
                    <SortIcon field={Object.keys(mockData[0])[index + 1] as keyof Beneficiary} />
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {mockData.map((beneficiary) => (
              <tr key={beneficiary.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <input
                    type="checkbox"
                    checked={selectedRows.includes(beneficiary.id)}
                    onChange={() => handleSelectRow(beneficiary.id)}
                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <button
                    onClick={() => navigate(`/beneficiaire/${beneficiary.id}`)}
                    className="text-indigo-600 hover:text-indigo-900 flex items-center gap-1"
                  >
                    #{beneficiary.id}
                    <ExternalLink size={14} />
                  </button>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{beneficiary.email}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{beneficiary.lastName}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{beneficiary.firstName}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{beneficiary.civility}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {new Date(beneficiary.birthDate).toLocaleDateString('fr-FR')}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{beneficiary.phone}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex gap-1">
                    {beneficiary.tags.map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {new Date(beneficiary.lastInteraction).toLocaleDateString('fr-FR')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default BeneficiaryTable;