export interface IncomeSource {
  category: string;
  subCategory: string;
  amount: number;
  frequency: 'monthly' | 'quarterly' | 'annual';
  startDate?: string;
  endDate?: string;
}

export interface Expense {
  category: string;
  subCategory: string;
  amount: number;
  frequency: 'monthly' | 'quarterly' | 'annual';
  mandatory: boolean;
  paid: boolean;
  dueDate?: string;
}

export interface FinancialData {
  month: string;
  incomes: {
    [key: string]: number;
  };
  expenses: {
    [key: string]: number;
  };
  total: number;
}