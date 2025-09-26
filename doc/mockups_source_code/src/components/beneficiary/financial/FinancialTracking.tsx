import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import type { FinancialData } from '../../../types/financial';

const mockFinancialData: FinancialData[] = [
  {
    month: 'Jan',
    incomes: {
      'RSA': 598.54,
      'Prime d\'activité': 200,
      'APL': 250,
      'Salaire': 800,
      'Aide familiale': 100
    },
    expenses: {
      'Loyer': -450,
      'Énergie': -80,
      'Assurance habitation': -15,
      'Mutuelle santé': -30,
      'Transport': -75
    },
    total: 1298.54
  },
  {
    month: 'Fév',
    incomes: {
      'RSA': 598.54,
      'Prime d\'activité': 200,
      'APL': 250,
      'Salaire': 850,
      'Aide familiale': 100
    },
    expenses: {
      'Loyer': -450,
      'Énergie': -85,
      'Assurance habitation': -15,
      'Mutuelle santé': -30,
      'Transport': -75
    },
    total: 1343.54
  },
  {
    month: 'Mar',
    incomes: {
      'RSA': 598.54,
      'Prime d\'activité': 200,
      'APL': 250,
      'Salaire': 900,
      'Aide familiale': 150
    },
    expenses: {
      'Loyer': -450,
      'Énergie': -70,
      'Assurance habitation': -15,
      'Mutuelle santé': -30,
      'Transport': -75
    },
    total: 1458.54
  }
];

const INCOME_COLORS = {
  'RSA': '#4F46E5',
  'Prime d\'activité': '#10B981',
  'APL': '#F59E0B',
  'Salaire': '#6366F1',
  'Aide familiale': '#8B5CF6'
};

const EXPENSE_COLORS = {
  'Loyer': '#EF4444',
  'Énergie': '#F97316',
  'Assurance habitation': '#F43F5E',
  'Mutuelle santé': '#EC4899',
  'Transport': '#D946EF'
};

const FinancialTracking: React.FC = () => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR'
    }).format(value);
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 border border-gray-200 shadow-lg rounded-lg">
          <p className="font-semibold mb-2">{label}</p>
          {payload.map((entry: any) => (
            <div key={entry.name} className="flex items-center gap-2 text-sm">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: entry.color }}
              />
              <span>{entry.name}:</span>
              <span className="font-medium">
                {formatCurrency(Math.abs(entry.value))}
              </span>
            </div>
          ))}
          {payload[0]?.payload?.total && (
            <div className="mt-2 pt-2 border-t border-gray-200">
              <div className="flex items-center justify-between text-sm font-semibold">
                <span>Total net:</span>
                <span>{formatCurrency(payload[0].payload.total)}</span>
              </div>
            </div>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h2 className="text-xl font-semibold mb-6">Suivi Financier</h2>
      <div className="h-[500px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={mockFinancialData}
            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis tickFormatter={(value) => `${value}€`} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            {/* Income Bars */}
            {Object.entries(INCOME_COLORS).map(([key, color]) => (
              <Bar
                key={key}
                dataKey={`incomes.${key}`}
                name={key}
                stackId="income"
                fill={color}
              />
            ))}
            {/* Expense Bars */}
            {Object.entries(EXPENSE_COLORS).map(([key, color]) => (
              <Bar
                key={key}
                dataKey={`expenses.${key}`}
                name={key}
                stackId="expense"
                fill={color}
              />
            ))}
            {/* Total Line */}
            <Bar
              dataKey="total"
              name="Total Net"
              fill="#047857"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
      
      <div className="mt-6 grid grid-cols-2 gap-6">
        <div>
          <h3 className="text-lg font-medium mb-3">Revenus Mensuels</h3>
          <div className="space-y-2">
            {Object.entries(mockFinancialData[2].incomes).map(([source, amount]) => (
              <div key={source} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: INCOME_COLORS[source as keyof typeof INCOME_COLORS] }}
                  />
                  <span>{source}</span>
                </div>
                <span className="font-medium">{formatCurrency(amount)}</span>
              </div>
            ))}
            <div className="pt-2 mt-2 border-t border-gray-200">
              <div className="flex items-center justify-between font-semibold">
                <span>Total Net:</span>
                <span>{formatCurrency(mockFinancialData[2].total)}</span>
              </div>
            </div>
          </div>
        </div>
        
        <div>
          <h3 className="text-lg font-medium mb-3">Charges Mensuelles</h3>
          <div className="space-y-2">
            {Object.entries(mockFinancialData[2].expenses).map(([source, amount]) => (
              <div key={source} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: EXPENSE_COLORS[source as keyof typeof EXPENSE_COLORS] }}
                  />
                  <span>{source}</span>
                </div>
                <span className="font-medium text-red-600">{formatCurrency(Math.abs(amount))}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FinancialTracking;