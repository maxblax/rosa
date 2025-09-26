import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const mockData = [
  { 
    month: 'Jan',
    'Banque Alimentaire': 120,
    'Croix Rouge': 85,
    'Restos du Cœur': 95
  },
  { 
    month: 'Fév',
    'Banque Alimentaire': 135,
    'Croix Rouge': 90,
    'Restos du Cœur': 100
  },
  { 
    month: 'Mar',
    'Banque Alimentaire': 125,
    'Croix Rouge': 95,
    'Restos du Cœur': 105
  },
  { 
    month: 'Avr',
    'Banque Alimentaire': 140,
    'Croix Rouge': 88,
    'Restos du Cœur': 98
  },
  { 
    month: 'Mai',
    'Banque Alimentaire': 150,
    'Croix Rouge': 92,
    'Restos du Cœur': 110
  },
  { 
    month: 'Jun',
    'Banque Alimentaire': 145,
    'Croix Rouge': 96,
    'Restos du Cœur': 115
  }
];

const PartnerDeliveriesChart: React.FC = () => {
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm">
      <h2 className="text-lg font-semibold mb-4">Produits Délivrés par Partenaires</h2>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={mockData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="Banque Alimentaire" stackId="a" fill="#4F46E5" />
            <Bar dataKey="Croix Rouge" stackId="a" fill="#10B981" />
            <Bar dataKey="Restos du Cœur" stackId="a" fill="#F59E0B" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default PartnerDeliveriesChart;