import React, { useState } from 'react';
import { Search, ChevronDown, ChevronUp } from 'lucide-react';

interface Volunteer {
  id: number;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  beneficiariesCount: number;
  monthlyHours: number;
  role: 'Bénévole' | 'Administrateur';
}

const mockVolunteers: Volunteer[] = [
  {
    id: 1,
    firstName: 'Marie',
    lastName: 'Dubois',
    email: 'marie.dubois@email.com',
    phone: '06 12 34 56 78',
    beneficiariesCount: 15,
    monthlyHours: 24,
    role: 'Administrateur'
  },
  {
    id: 2,
    firstName: 'Jean',
    lastName: 'Martin',
    email: 'jean.martin@email.com',
    phone: '06 23 45 67 89',
    beneficiariesCount: 8,
    monthlyHours: 16,
    role: 'Bénévole'
  },
  {
    id: 3,
    firstName: 'Sophie',
    lastName: 'Laurent',
    email: 'sophie.laurent@email.com',
    phone: '06 34 56 78 90',
    beneficiariesCount: 12,
    monthlyHours: 20,
    role: 'Bénévole'
  },
  {
    id: 4,
    firstName: 'Pierre',
    lastName: 'Bernard',
    email: 'pierre.bernard@email.com',
    phone: '06 45 67 89 01',
    beneficiariesCount: 18,
    monthlyHours: 28,
    role: 'Administrateur'
  },
  {
    id: 5,
    firstName: 'Claire',
    lastName: 'Moreau',
    email: 'claire.moreau@email.com',
    phone: '06 56 78 90 12',
    beneficiariesCount: 6,
    monthlyHours: 12,
    role: 'Bénévole'
  }
];

const VolunteerTable: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<keyof Volunteer>('lastName');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  const handleSort = (field: keyof Volunteer) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const filteredVolunteers = mockVolunteers
    .filter(volunteer => 
      volunteer.firstName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      volunteer.lastName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      volunteer.email.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => {
      const aValue = a[sortField];
      const bValue = b[sortField];
      
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortDirection === 'asc' 
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }
      
      return sortDirection === 'asc'
        ? (aValue as number) - (bValue as number)
        : (bValue as number) - (aValue as number);
    });

  const SortIcon = ({ field }: { field: keyof Volunteer }) => {
    if (sortField !== field) return null;
    return sortDirection === 'asc' ? <ChevronUp size={16} /> : <ChevronDown size={16} />;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm">
      <div className="p-4 border-b border-gray-200">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            placeholder="Rechercher un bénévole..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {[
                { key: 'lastName', label: 'Nom' },
                { key: 'firstName', label: 'Prénom' },
                { key: 'email', label: 'Email' },
                { key: 'phone', label: 'Téléphone' },
                { key: 'beneficiariesCount', label: 'Bénéficiaires Référencés' },
                { key: 'monthlyHours', label: 'Heures (dernier mois)' },
                { key: 'role', label: 'Rôle' }
              ].map((column) => (
                <th
                  key={column.key}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                  onClick={() => handleSort(column.key as keyof Volunteer)}
                >
                  <div className="flex items-center gap-1">
                    {column.label}
                    <SortIcon field={column.key as keyof Volunteer} />
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredVolunteers.map((volunteer) => (
              <tr key={volunteer.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {volunteer.lastName}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {volunteer.firstName}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {volunteer.email}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {volunteer.phone}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {volunteer.beneficiariesCount}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {volunteer.monthlyHours}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    volunteer.role === 'Administrateur'
                      ? 'bg-purple-100 text-purple-800'
                      : 'bg-blue-100 text-blue-800'
                  }`}>
                    {volunteer.role}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default VolunteerTable;