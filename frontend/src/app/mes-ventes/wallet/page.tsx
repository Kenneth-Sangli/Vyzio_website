'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Header, Footer } from '@/components/layout';
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/stores/auth-store';
import { api, formatPrice } from '@/lib/api';
import {
  Wallet,
  ArrowDownToLine,
  ArrowUpFromLine,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  ChevronRight,
  CreditCard,
  Building2,
  Plus,
  History,
  DollarSign,
  Package,
  RefreshCw,
} from 'lucide-react';

interface WalletData {
  id: string;
  balance: string;
  pending_balance: string;
  total_earned: string;
  total_withdrawn: string;
  bank_name: string;
  account_holder: string;
  iban: string;
  bic: string;
}

interface Transaction {
  id: string;
  transaction_type: string;
  amount: string;
  balance_after: string;
  description: string;
  created_at: string;
  order_number?: string;
}

interface WithdrawalRequest {
  id: string;
  amount: string;
  status: string;
  status_display: string;
  created_at: string;
  processed_at: string | null;
  completed_at: string | null;
  rejection_reason: string;
}

const transactionTypeConfig: Record<string, { color: string; icon: any; label: string }> = {
  sale: { color: 'text-green-600', icon: ArrowDownToLine, label: 'Vente' },
  withdrawal: { color: 'text-red-600', icon: ArrowUpFromLine, label: 'Retrait' },
  refund: { color: 'text-orange-600', icon: RefreshCw, label: 'Remboursement' },
  adjustment: { color: 'text-blue-600', icon: DollarSign, label: 'Ajustement' },
  fee: { color: 'text-gray-600', icon: DollarSign, label: 'Frais' },
};

const withdrawalStatusConfig: Record<string, { color: string; icon: any }> = {
  pending: { color: 'bg-yellow-100 text-yellow-800', icon: Clock },
  processing: { color: 'bg-blue-100 text-blue-800', icon: RefreshCw },
  completed: { color: 'bg-green-100 text-green-800', icon: CheckCircle },
  rejected: { color: 'bg-red-100 text-red-800', icon: AlertCircle },
  cancelled: { color: 'bg-gray-100 text-gray-800', icon: AlertCircle },
};

export default function WalletPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [wallet, setWallet] = useState<WalletData | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [withdrawals, setWithdrawals] = useState<WithdrawalRequest[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'transactions' | 'withdrawals'>('transactions');
  const [showBankForm, setShowBankForm] = useState(false);
  const [showWithdrawForm, setShowWithdrawForm] = useState(false);
  const [bankForm, setBankForm] = useState({
    bank_name: '',
    account_holder: '',
    iban: '',
    bic: '',
  });
  const [withdrawAmount, setWithdrawAmount] = useState('');

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/connexion?redirect=/mes-ventes/wallet');
      return;
    }
    fetchData();
  }, [isAuthenticated]);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      const [walletRes, transactionsRes, withdrawalsRes] = await Promise.all([
        api.get('/orders/wallet/me/'),
        api.get('/orders/wallet/transactions/'),
        api.get('/orders/withdrawals/'),
      ]);
      setWallet(walletRes.data);
      setTransactions(transactionsRes.data.results || transactionsRes.data || []);
      setWithdrawals(withdrawalsRes.data.results || withdrawalsRes.data || []);
      
      if (walletRes.data) {
        setBankForm({
          bank_name: walletRes.data.bank_name || '',
          account_holder: walletRes.data.account_holder || '',
          iban: walletRes.data.iban || '',
          bic: walletRes.data.bic || '',
        });
      }
    } catch (error) {
      console.error('Erreur chargement wallet:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveBankDetails = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/orders/wallet/bank-details/', bankForm);
      setShowBankForm(false);
      fetchData();
      alert('Informations bancaires enregistrées !');
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de l\'enregistrement');
    }
  };

  const handleRequestWithdrawal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!withdrawAmount || parseFloat(withdrawAmount) <= 0) {
      alert('Veuillez entrer un montant valide');
      return;
    }

    if (!wallet?.iban) {
      alert('Veuillez d\'abord renseigner vos informations bancaires');
      setShowBankForm(true);
      return;
    }

    try {
      await api.post('/orders/withdrawals/', {
        amount: withdrawAmount,
      });
      setShowWithdrawForm(false);
      setWithdrawAmount('');
      fetchData();
      alert('Demande de retrait envoyée ! Nous la traiterons dans les plus brefs délais.');
    } catch (error: any) {
      console.error('Erreur:', error);
      alert(error.response?.data?.detail || 'Erreur lors de la demande');
    }
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />
      
      <main className="flex-1 container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
          <div>
            <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
              <Link href="/dashboard" className="hover:text-gray-700">Dashboard</Link>
              <ChevronRight className="h-4 w-4" />
              <Link href="/mes-ventes" className="hover:text-gray-700">Mes Ventes</Link>
              <ChevronRight className="h-4 w-4" />
              <span>Portefeuille</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Mon Portefeuille</h1>
            <p className="text-gray-600 mt-1">
              Gérez vos revenus et demandez des retraits
            </p>
          </div>
        </div>

        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-gray-500 mt-4">Chargement...</p>
          </div>
        ) : (
          <>
            {/* Cartes de stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-6 text-white shadow-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-green-100 text-sm">Solde disponible</div>
                    <div className="text-3xl font-bold mt-1">
                      {wallet ? formatPrice(parseFloat(wallet.balance)) : '0 €'}
                    </div>
                  </div>
                  <Wallet className="h-10 w-10 text-green-200" />
                </div>
                {parseFloat(wallet?.balance || '0') >= 10 && (
                  <Button
                    className="mt-4 w-full bg-white/20 hover:bg-white/30 text-white"
                    onClick={() => setShowWithdrawForm(true)}
                  >
                    <ArrowUpFromLine className="h-4 w-4 mr-2" />
                    Demander un retrait
                  </Button>
                )}
              </div>

              <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-gray-500 text-sm">En attente</div>
                    <div className="text-2xl font-bold text-yellow-600 mt-1">
                      {wallet ? formatPrice(parseFloat(wallet.pending_balance)) : '0 €'}
                    </div>
                  </div>
                  <Clock className="h-8 w-8 text-yellow-500" />
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  Libéré après confirmation de réception
                </p>
              </div>

              <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-gray-500 text-sm">Total gagné</div>
                    <div className="text-2xl font-bold text-gray-900 mt-1">
                      {wallet ? formatPrice(parseFloat(wallet.total_earned)) : '0 €'}
                    </div>
                  </div>
                  <TrendingUp className="h-8 w-8 text-green-500" />
                </div>
              </div>

              <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-gray-500 text-sm">Total retiré</div>
                    <div className="text-2xl font-bold text-gray-900 mt-1">
                      {wallet ? formatPrice(parseFloat(wallet.total_withdrawn)) : '0 €'}
                    </div>
                  </div>
                  <ArrowUpFromLine className="h-8 w-8 text-blue-500" />
                </div>
              </div>
            </div>

            {/* Informations bancaires */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm mb-8">
              <div className="p-4 border-b border-gray-200 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Building2 className="h-5 w-5 text-gray-600" />
                  <h2 className="font-semibold text-gray-900">Informations bancaires</h2>
                </div>
                <Button size="sm" variant="outline" onClick={() => setShowBankForm(true)}>
                  {wallet?.iban ? 'Modifier' : 'Ajouter'}
                </Button>
              </div>
              <div className="p-4">
                {wallet?.iban ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Banque:</span>
                      <span className="ml-2 font-medium">{wallet.bank_name || '-'}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Titulaire:</span>
                      <span className="ml-2 font-medium">{wallet.account_holder || '-'}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">IBAN:</span>
                      <span className="ml-2 font-medium font-mono">
                        {wallet.iban.replace(/(.{4})/g, '$1 ').trim()}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">BIC:</span>
                      <span className="ml-2 font-medium font-mono">{wallet.bic || '-'}</span>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-4 text-gray-500">
                    <CreditCard className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                    <p>Aucune information bancaire enregistrée</p>
                    <p className="text-sm">Ajoutez vos coordonnées pour recevoir vos paiements</p>
                  </div>
                )}
              </div>
            </div>

            {/* Tabs: Transactions / Retraits */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
              <div className="border-b border-gray-200">
                <div className="flex">
                  <button
                    className={`flex-1 py-3 px-4 text-sm font-medium text-center border-b-2 transition-colors ${
                      activeTab === 'transactions'
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                    onClick={() => setActiveTab('transactions')}
                  >
                    <History className="h-4 w-4 inline mr-2" />
                    Historique des transactions
                  </button>
                  <button
                    className={`flex-1 py-3 px-4 text-sm font-medium text-center border-b-2 transition-colors ${
                      activeTab === 'withdrawals'
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                    onClick={() => setActiveTab('withdrawals')}
                  >
                    <ArrowUpFromLine className="h-4 w-4 inline mr-2" />
                    Demandes de retrait
                  </button>
                </div>
              </div>

              <div className="p-4">
                {activeTab === 'transactions' ? (
                  transactions.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <History className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                      <p>Aucune transaction</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {transactions.map((tx) => {
                        const config = transactionTypeConfig[tx.transaction_type] || transactionTypeConfig.adjustment;
                        const Icon = config.icon;
                        return (
                          <div key={tx.id} className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg">
                            <div className="flex items-center gap-3">
                              <div className={`p-2 rounded-full bg-gray-100 ${config.color}`}>
                                <Icon className="h-4 w-4" />
                              </div>
                              <div>
                                <div className="font-medium text-gray-900">{tx.description}</div>
                                <div className="text-xs text-gray-500">
                                  {new Date(tx.created_at).toLocaleDateString('fr-FR', {
                                    day: 'numeric',
                                    month: 'short',
                                    year: 'numeric',
                                    hour: '2-digit',
                                    minute: '2-digit',
                                  })}
                                </div>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className={`font-semibold ${parseFloat(tx.amount) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {parseFloat(tx.amount) >= 0 ? '+' : ''}{formatPrice(parseFloat(tx.amount))}
                              </div>
                              <div className="text-xs text-gray-500">
                                Solde: {formatPrice(parseFloat(tx.balance_after))}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )
                ) : (
                  withdrawals.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <ArrowUpFromLine className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                      <p>Aucune demande de retrait</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {withdrawals.map((wd) => {
                        const config = withdrawalStatusConfig[wd.status] || withdrawalStatusConfig.pending;
                        const Icon = config.icon;
                        return (
                          <div key={wd.id} className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg">
                            <div className="flex items-center gap-3">
                              <div className={`p-2 rounded-full ${config.color}`}>
                                <Icon className="h-4 w-4" />
                              </div>
                              <div>
                                <div className="font-medium text-gray-900">
                                  Demande de retrait
                                </div>
                                <div className="text-xs text-gray-500">
                                  {new Date(wd.created_at).toLocaleDateString('fr-FR', {
                                    day: 'numeric',
                                    month: 'short',
                                    year: 'numeric',
                                  })}
                                </div>
                                {wd.rejection_reason && (
                                  <div className="text-xs text-red-600 mt-1">
                                    Raison: {wd.rejection_reason}
                                  </div>
                                )}
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="font-semibold text-gray-900">
                                {formatPrice(parseFloat(wd.amount))}
                              </div>
                              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs ${config.color}`}>
                                {wd.status_display}
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )
                )}
              </div>
            </div>
          </>
        )}

        {/* Modal: Formulaire bancaire */}
        {showBankForm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl w-full max-w-md p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">Informations bancaires</h3>
              <form onSubmit={handleSaveBankDetails} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nom de la banque
                  </label>
                  <input
                    type="text"
                    value={bankForm.bank_name}
                    onChange={(e) => setBankForm({ ...bankForm, bank_name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Ex: BNP Paribas"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Titulaire du compte
                  </label>
                  <input
                    type="text"
                    value={bankForm.account_holder}
                    onChange={(e) => setBankForm({ ...bankForm, account_holder: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Ex: Jean Dupont"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    IBAN
                  </label>
                  <input
                    type="text"
                    value={bankForm.iban}
                    onChange={(e) => setBankForm({ ...bankForm, iban: e.target.value.replace(/\s/g, '').toUpperCase() })}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                    placeholder="FR76 1234 5678 9012 3456 7890 123"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    BIC/SWIFT
                  </label>
                  <input
                    type="text"
                    value={bankForm.bic}
                    onChange={(e) => setBankForm({ ...bankForm, bic: e.target.value.toUpperCase() })}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                    placeholder="BNPAFRPP"
                  />
                </div>
                <div className="flex gap-3 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    className="flex-1"
                    onClick={() => setShowBankForm(false)}
                  >
                    Annuler
                  </Button>
                  <Button type="submit" variant="gradient" className="flex-1">
                    Enregistrer
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Demande de retrait */}
        {showWithdrawForm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl w-full max-w-md p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">Demander un retrait</h3>
              <form onSubmit={handleRequestWithdrawal} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Montant à retirer
                  </label>
                  <div className="relative">
                    <input
                      type="number"
                      step="0.01"
                      min="10"
                      max={wallet?.balance || 0}
                      value={withdrawAmount}
                      onChange={(e) => setWithdrawAmount(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="0.00"
                      required
                    />
                    <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500">€</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Disponible: {wallet ? formatPrice(parseFloat(wallet.balance)) : '0 €'} (min. 10 €)
                  </p>
                </div>
                <div className="bg-blue-50 p-3 rounded-lg">
                  <p className="text-sm text-blue-800">
                    <strong>Information:</strong> Les retraits sont traités manuellement sous 3-5 jours ouvrés.
                    Vous recevrez un email de confirmation une fois le virement effectué.
                  </p>
                </div>
                <div className="flex gap-3 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    className="flex-1"
                    onClick={() => setShowWithdrawForm(false)}
                  >
                    Annuler
                  </Button>
                  <Button type="submit" variant="gradient" className="flex-1">
                    Demander le retrait
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}
