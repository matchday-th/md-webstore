<template>
  <div class="min-h-screen bg-ink text-white">
    <div class="mx-auto max-w-7xl px-6 py-8 lg:px-10">
      <header class="panel mb-8 overflow-hidden">
        <div class="grid gap-4 px-6 py-6 lg:grid-cols-5 lg:px-8">
          <div class="rounded-[1.6rem] border border-white/10 bg-white/[0.03] p-4">
            <p class="text-xs uppercase tracking-[0.2em] text-white/35">Profiles</p>
            <p class="mt-3 text-3xl font-semibold">{{ profiles.length }}</p>
          </div>
          <div class="rounded-[1.6rem] border border-white/10 bg-white/[0.03] p-4">
            <p class="text-xs uppercase tracking-[0.2em] text-white/35">Products</p>
            <p class="mt-3 text-3xl font-semibold">{{ products.length }}</p>
          </div>
          <div class="rounded-[1.6rem] border border-white/10 bg-white/[0.03] p-4">
            <p class="text-xs uppercase tracking-[0.2em] text-white/35">Orders</p>
            <p class="mt-3 text-3xl font-semibold">{{ orders.length }}</p>
          </div>
          <div class="rounded-[1.6rem] border border-white/10 bg-white/[0.03] p-4">
            <p class="text-xs uppercase tracking-[0.2em] text-white/35">Inventory Value</p>
            <p class="mt-3 text-3xl font-semibold">{{ money(inventoryValue) }}</p>
          </div>
        </div>
      </header>

      <main v-if="ready && !errorMessage" class="space-y-8">
        <section class="panel overflow-hidden p-0">
          <div class="border-b border-white/10 bg-white px-6 text-ink">
            <div class="flex flex-wrap items-end gap-0 overflow-x-auto">
              <button
                class="border-b-2 px-6 py-5 text-lg font-semibold transition"
                :class="workspaceTab === 'storefront' ? 'border-red-500 text-red-500' : 'border-transparent text-ink/55 hover:text-ink'"
                @click="workspaceTab = 'storefront'"
              >
                หน้าร้าน
              </button>
              <button
                class="border-b-2 px-6 py-5 text-lg font-semibold transition"
                :class="workspaceTab === 'warehouse' ? 'border-red-500 text-red-500' : 'border-transparent text-ink/55 hover:text-ink'"
                @click="workspaceTab = 'warehouse'"
              >
                คลัง
              </button>
              <button
                class="border-b-2 px-6 py-5 text-lg font-semibold transition"
                :class="workspaceTab === 'orders' ? 'border-red-500 text-red-500' : 'border-transparent text-ink/55 hover:text-ink'"
                @click="workspaceTab = 'orders'"
              >
                บิลออเดอร์
              </button>
              <button
                class="border-b-2 px-6 py-5 text-lg font-semibold transition"
                :class="workspaceTab === 'user' ? 'border-red-500 text-red-500' : 'border-transparent text-ink/55 hover:text-ink'"
                @click="workspaceTab = 'user'"
              >
                สมาชิก
              </button>
            </div>
          </div>

          <div class="p-6">
            <section v-if="workspaceTab === 'storefront'" class="space-y-6">
              <article class="rounded-[2rem] border border-white/10 bg-black/20 p-6">
                <div class="panel-header">
                  <div>
                    <p class="text-xs uppercase tracking-[0.22em] text-white/40">Banner Listing</p>
                    <h2 class="mt-2 text-2xl font-semibold">Featured products drive the storefront.</h2>
                  </div>
                  <MegaphoneIcon class="h-6 w-6 text-white/55" />
                </div>

                <div class="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
                  <div
                    v-for="product in featuredProducts"
                    :key="product.id"
                    class="rounded-[1.8rem] border border-white/10 bg-black/20 p-5"
                  >
                    <div class="flex items-start justify-between gap-3">
                      <div>
                        <p class="text-lg font-medium">{{ product.name }}</p>
                        <p class="mt-1 text-sm text-white/50">{{ product.description }}</p>
                      </div>
                      <span class="chip">{{ product.category }}</span>
                    </div>

                    <div class="mt-5">
                      <p class="text-xs uppercase tracking-[0.2em] text-white/35">Price</p>
                      <p class="mt-1 text-xl font-semibold">{{ money(product.price) }}</p>
                    </div>
                  </div>
                </div>
              </article>

              <article class="rounded-[2rem] border border-white/10 bg-black/20 p-6">
                <div class="panel-header">
                  <div>
                    <p class="text-xs uppercase tracking-[0.22em] text-white/40">Store Directory</p>
                    <h2 class="mt-2 text-2xl font-semibold">Manage storefront shops from the same workspace.</h2>
                  </div>
                  <div class="flex items-center gap-3">
                    <button class="button-primary" type="button" @click="openShopModal">Create Shop</button>
                    <ClipboardDocumentListIcon class="h-6 w-6 text-white/55" />
                  </div>
                </div>

                <div class="mb-4 flex flex-wrap items-end gap-4">
                  <div class="min-w-[260px] flex-1">
                    <label class="label">Owner Provider</label>
                    <select v-model="shopForm.provider_id" class="field">
                      <option value="" disabled>Select provider</option>
                      <option v-for="provider in providers" :key="provider.provider_id" :value="provider.provider_id">
                        {{ provider.provider_name }} · {{ provider.shop_count || 0 }} shops
                      </option>
                    </select>
                  </div>
                  <div v-if="shopMessage" class="rounded-[1.2rem] border border-emerald-400/20 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-100">
                    {{ shopMessage }}
                  </div>
                </div>

                <div v-if="selectedProviderInfo && selectedProviderInfo.shop_names?.length" class="mb-5 flex flex-wrap gap-2">
                  <span
                    v-for="shopName in selectedProviderInfo.shop_names"
                    :key="shopName"
                    class="rounded-full border border-white/10 px-3 py-1 text-xs text-white/60"
                  >
                    {{ shopName }}
                  </span>
                </div>

                <div v-if="selectedProviderShops.length" class="space-y-3">
                  <div
                    v-for="shop in selectedProviderShops"
                    :key="shop.provider_id"
                    class="rounded-[1.5rem] border border-white/10 bg-white/[0.025] px-4 py-4"
                  >
                    <div class="flex items-start justify-between gap-3">
                      <div>
                        <p class="font-medium">{{ shop.provider_name }}</p>
                        <p class="mt-1 text-sm text-white/45">{{ shop.provider_id }}</p>
                        <p class="mt-2 text-xs uppercase tracking-[0.16em] text-white/35">{{ shop.product_count || 0 }} products in this shop</p>
                      </div>
                      <div class="flex items-center gap-2">
                        <span class="chip">store</span>
                        <button
                          v-if="shop.owner_provider_id"
                          class="rounded-full border border-red-400/20 bg-red-400/10 px-3 py-1 text-xs text-red-200 transition hover:bg-red-400/20"
                          type="button"
                          @click="removeShop(shop)"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
                <div v-else class="rounded-[1.5rem] border border-dashed border-white/10 px-4 py-8 text-center text-sm text-white/40">
                  No shops loaded for this provider yet.
                </div>
              </article>
            </section>

            <section v-else-if="workspaceTab === 'warehouse'" class="rounded-[2rem] border border-white/10 bg-black/20 p-6">
              <div class="panel-header">
                <div>
                  <p class="text-xs uppercase tracking-[0.22em] text-white/40">Warehouse</p>
                  <h2 class="mt-2 text-2xl font-semibold">Inventory updates directly from product and order activity.</h2>
                </div>
                <ArchiveBoxIcon class="h-6 w-6 text-white/55" />
              </div>

              <div class="space-y-3">
                <div
                  v-for="product in products"
                  :key="product.id"
                  class="flex items-center justify-between rounded-[1.4rem] border border-white/10 bg-white/[0.025] px-4 py-4"
                >
                  <div>
                    <p class="font-medium">{{ product.name }}</p>
                    <p class="mt-1 text-sm text-white/45">{{ product.sku }} · {{ product.category }}</p>
                  </div>
                  <div class="text-right">
                    <p class="text-lg font-semibold">{{ product.stock }} units</p>
                    <p
                      class="mt-1 text-xs uppercase tracking-[0.16em]"
                      :class="Number(product.stock) <= 5 ? 'text-amber-300' : 'text-white/35'"
                    >
                      {{ Number(product.stock) <= 5 ? "Low stock" : "Healthy stock" }}
                    </p>
                  </div>
                </div>
              </div>
            </section>

            <section v-else-if="workspaceTab === 'orders'" class="rounded-[2rem] border border-white/10 bg-black/20 p-6">
              <div class="panel-header">
                <div>
                  <p class="text-xs uppercase tracking-[0.22em] text-white/40">Sales History</p>
                  <h2 class="mt-2 text-2xl font-semibold">Review completed order flow in a provider-style sales ledger.</h2>
                </div>
                <ClipboardDocumentListIcon class="h-6 w-6 text-white/55" />
              </div>

              <div v-if="orders.length" class="overflow-hidden rounded-[1.8rem] border border-white/10 bg-white/[0.025]">
                <div class="overflow-x-auto">
                  <table class="min-w-full divide-y divide-white/10 text-sm">
                    <thead class="bg-white/[0.05] text-left text-xs font-semibold uppercase tracking-[0.2em] text-white/45">
                      <tr>
                        <th class="px-5 py-4">#</th>
                        <th class="px-5 py-4">Date</th>
                        <th class="px-5 py-4">Invoice</th>
                        <th class="px-5 py-4">Customer</th>
                        <th class="px-5 py-4">Payment</th>
                        <th class="px-5 py-4">Method</th>
                        <th class="px-5 py-4">Total</th>
                        <th class="px-5 py-4">Action</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-white/5 bg-transparent">
                      <tr
                        v-for="(order, index) in orders"
                        :key="order.id"
                        class="transition hover:bg-white/[0.03]"
                      >
                        <td class="px-5 py-4 text-white/45">{{ index + 1 }}</td>
                        <td class="px-5 py-4 text-white/65">{{ formatDate(order.created_at) }}</td>
                        <td class="px-5 py-4">
                          <div class="font-medium text-white">{{ order.invoice_number || '-' }}</div>
                          <div class="mt-1 text-xs text-white/40">Order #{{ order.id }}</div>
                        </td>
                        <td class="px-5 py-4">
                          <div class="font-medium text-white">{{ order.user_name || '-' }}</div>
                          <div class="mt-1 text-xs text-white/40">{{ order.customer_email || '-' }}</div>
                        </td>
                        <td class="px-5 py-4">
                          <span class="inline-flex rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em]" :class="paymentBadgeClass(order.payment_status)">
                            {{ prettyPaymentStatus(order.payment_status) }}
                          </span>
                        </td>
                        <td class="px-5 py-4 text-white/60">{{ prettyLabel(order.payment_method) }}</td>
                        <td class="px-5 py-4 font-medium text-white">{{ money(order.total) }}</td>
                        <td class="px-5 py-4">
                          <button class="button-primary" type="button" @click="openOrderBill(order)">
                            ดูบิล
                          </button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
              <div v-else class="rounded-[1.5rem] border border-dashed border-white/10 px-4 py-8 text-center text-sm text-white/40">
                No sales history yet.
              </div>
            </section>

            <section v-else class="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
              <article class="rounded-[2rem] border border-white/10 bg-black/20 p-6">
                <div class="panel-header">
                  <div>
                    <p class="text-xs uppercase tracking-[0.22em] text-white/40">User</p>
                    <h2 class="mt-2 text-2xl font-semibold">Member profile manager.</h2>
                  </div>
                  <UserCircleIcon class="h-6 w-6 text-white/55" />
                </div>

                <form class="space-y-3" @submit.prevent="submitProfile">
                  <div>
                    <label class="label">Full Name</label>
                    <input v-model="profileForm.name" class="field" type="text" required />
                  </div>
                  <div class="grid gap-3 md:grid-cols-2">
                    <div>
                      <label class="label">Email</label>
                      <input v-model="profileForm.email" class="field" type="email" required />
                    </div>
                    <div>
                      <label class="label">Role</label>
                      <input v-model="profileForm.role" class="field" type="text" required />
                    </div>
                  </div>
                  <div>
                    <label class="label">Phone</label>
                    <input v-model="profileForm.phone" class="field" type="text" />
                  </div>
                  <div>
                    <label class="label">Address</label>
                    <textarea v-model="profileForm.address" class="field min-h-[110px]"></textarea>
                  </div>
                  <div class="flex flex-wrap gap-3">
                    <button class="button-primary" type="submit">{{ profileForm.id ? "Update Profile" : "Create Profile" }}</button>
                    <button class="button-secondary" type="button" @click="resetProfileForm">Reset</button>
                    <button v-if="profileForm.id" class="button-danger" type="button" @click="removeProfile(profileForm.id)">Delete</button>
                  </div>
                </form>
              </article>

              <article class="rounded-[2rem] border border-white/10 bg-black/20 p-4">
                <div class="space-y-3">
                  <button
                    v-for="profile in profiles"
                    :key="profile.id"
                    class="flex w-full items-center justify-between rounded-[1.4rem] border border-white/10 bg-white/[0.025] px-4 py-4 text-left transition hover:border-white/25"
                    @click="editProfile(profile)"
                  >
                    <div>
                      <p class="font-medium">{{ profile.name }}</p>
                      <p class="mt-1 text-sm text-white/45">{{ profile.role }} · {{ profile.email }}</p>
                    </div>
                    <ChevronRightIcon class="h-5 w-5 text-white/35" />
                  </button>
                </div>
              </article>
            </section>
          </div>
        </section>
      </main>

      <div v-else-if="errorMessage" class="panel p-12 text-center text-white/75">
        {{ errorMessage }}
      </div>
      <div v-else class="panel p-12 text-center text-white/60">Connecting to live database...</div>

      <div v-if="currentSalesBill" class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4 py-8 backdrop-blur-sm" @click.self="closeOrderBill">
        <div class="max-h-[calc(100vh-40px)] w-full max-w-6xl overflow-y-auto rounded-[2rem] border border-white/10 bg-[#161616] shadow-2xl">
          <div class="flex items-start justify-between gap-4 border-b border-white/10 px-8 py-7">
            <div>
              <p class="text-xs uppercase tracking-[0.22em] text-white/40">Bill Detail</p>
              <h2 class="mt-2 text-2xl font-semibold">🧾 Sales Bill</h2>
            </div>
            <button class="rounded-full border border-white/10 px-4 py-2 text-sm text-white/65 transition hover:text-white" type="button" @click="closeOrderBill">
              Close
            </button>
          </div>

          <div class="grid gap-0 lg:grid-cols-[1.2fr_0.9fr]">
            <div class="space-y-6 border-t border-white/10 px-8 py-8">
              <div class="flex flex-wrap items-center gap-3">
                <span class="rounded-full bg-white/10 px-4 py-2 text-sm font-semibold text-white/65">Created {{ formatDate(currentSalesBill.created_at) }}</span>
                <span class="rounded-full bg-emerald-400/15 px-4 py-2 text-sm font-semibold text-emerald-200">Bill Date: {{ formatShortDate(currentSalesBill.created_at) }}</span>
              </div>

              <div class="flex flex-wrap items-end justify-between gap-4">
                <div>
                  <div class="text-sm text-white/45">Invoice</div>
                  <div class="mt-1 text-3xl font-semibold tracking-tight text-white">{{ currentSalesBill.invoice_number || '-' }}</div>
                  <div class="mt-2 text-sm text-white/45">Order #{{ currentSalesBill.id }}</div>
                </div>
                <div class="text-right">
                  <div class="text-sm text-white/45">Customer</div>
                  <div class="mt-1 text-xl font-semibold text-white">{{ currentSalesBill.user_name || '-' }}</div>
                  <div class="text-sm text-white/45">{{ currentSalesBill.customer_email || '-' }}</div>
                </div>
              </div>

              <div class="overflow-hidden rounded-[1.6rem] border border-white/10 bg-white/[0.025]">
                <table class="min-w-full divide-y divide-white/10 text-sm">
                  <thead class="bg-white/[0.05] text-left text-xs font-semibold uppercase tracking-[0.2em] text-white/45">
                    <tr>
                      <th class="px-5 py-4">#</th>
                      <th class="px-5 py-4">Product</th>
                      <th class="px-5 py-4">SKU</th>
                      <th class="px-5 py-4">Qty</th>
                      <th class="px-5 py-4">Price</th>
                      <th class="px-5 py-4">Total</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-white/5">
                    <tr v-for="(item, index) in currentSalesBill.items" :key="currentSalesBill.id + '-' + item.productId">
                      <td class="px-5 py-4 text-white/45">{{ index + 1 }}</td>
                      <td class="px-5 py-4">
                        <div class="flex items-center gap-3">
                          <img v-if="item.image_url" :src="item.image_url" :alt="item.name" class="h-14 w-14 rounded-2xl object-cover" />
                          <div v-else class="flex h-14 w-14 items-center justify-center rounded-2xl border border-dashed border-white/10 bg-black/20 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/35">IMG</div>
                          <div>
                            <div class="font-medium text-white">{{ item.name }}</div>
                            <div class="text-xs text-white/40">{{ item.category || '-' }}</div>
                          </div>
                        </div>
                      </td>
                      <td class="px-5 py-4 text-white/60">{{ item.sku || '-' }}</td>
                      <td class="px-5 py-4 text-white/70">{{ item.quantity }}</td>
                      <td class="px-5 py-4 font-medium text-white">{{ money(item.price) }}</td>
                      <td class="px-5 py-4 font-medium text-white">{{ money(item.lineTotal || (item.quantity * item.price)) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div class="space-y-6 border-t border-l border-white/10 bg-white/[0.03] px-8 py-8">
              <div class="text-center">
                <div class="text-sm text-white/45">ยอดรวม</div>
                <div class="mt-2 text-5xl font-semibold tracking-tight text-white">{{ money(currentSalesBill.total) }}</div>
                <div class="mt-3 inline-flex rounded-full px-4 py-2 text-sm font-semibold uppercase tracking-[0.16em]" :class="paymentBadgeClass(currentSalesBill.payment_status)">
                  {{ prettyPaymentStatus(currentSalesBill.payment_status) }}
                </div>
              </div>

              <div class="rounded-[1.6rem] bg-black/20 p-5 shadow-sm">
                <div class="flex items-center justify-between text-sm text-white/50"><span>Subtotal</span><strong class="text-white">{{ money(currentSalesBill.pricing?.subtotal || currentSalesBill.total) }}</strong></div>
                <div class="mt-3 flex items-center justify-between text-sm text-white/50"><span>Discount</span><strong class="text-white">{{ money(currentSalesBill.pricing?.discount_amount || 0) }}</strong></div>
                <div class="mt-3 flex items-center justify-between text-sm text-white/50"><span>Before VAT</span><strong class="text-white">{{ money(currentSalesBill.pricing?.taxable_amount || currentSalesBill.total) }}</strong></div>
                <div class="mt-3 flex items-center justify-between text-sm text-white/50"><span>VAT / Tax</span><strong class="text-white">{{ money(currentSalesBill.pricing?.tax_amount || 0) }}</strong></div>
                <div class="mt-4 flex items-center justify-between border-t border-white/10 pt-4 text-base font-semibold text-white"><span>Grand Total</span><span>{{ money(currentSalesBill.pricing?.grand_total || currentSalesBill.total) }}</span></div>
              </div>

              <div class="rounded-[1.6rem] bg-black/20 p-5 shadow-sm">
                <div class="mb-4 flex items-center justify-between">
                  <h3 class="text-lg font-semibold text-white">Order Detail</h3>
                  <span class="text-xs uppercase tracking-[0.18em] text-white/35">{{ currentSalesBill.items.length }} items</span>
                </div>
                <div class="space-y-3 text-sm text-white/55">
                  <div class="flex items-center justify-between gap-3"><span>Method</span><strong class="text-white">{{ prettyLabel(currentSalesBill.payment_method) }}</strong></div>
                  <div class="flex items-start justify-between gap-3"><span>Shipping</span><strong class="max-w-[220px] text-right text-white">{{ currentSalesBill.shipping_address || '-' }}</strong></div>
                  <div class="flex items-start justify-between gap-3"><span>Notes</span><strong class="max-w-[220px] text-right text-white">{{ currentSalesBill.notes || '-' }}</strong></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="showShopModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4 py-8 backdrop-blur-sm" @click.self="closeShopModal">
        <div class="w-full max-w-2xl rounded-[2rem] border border-white/10 bg-[#161616] p-6 shadow-2xl">
          <div class="panel-header">
            <div>
              <p class="text-xs uppercase tracking-[0.22em] text-white/40">Store Setup</p>
              <h2 class="mt-2 text-2xl font-semibold">➕ Create Shop</h2>
            </div>
            <button class="rounded-full border border-white/10 px-4 py-2 text-sm text-white/65 transition hover:text-white" type="button" @click="closeShopModal">
              Close
            </button>
          </div>

          <form class="mt-6 space-y-4" @submit.prevent="submitShop">
            <div>
              <label class="label">Owner Provider</label>
              <select v-model="shopForm.provider_id" class="field" required>
                <option value="" disabled>Select provider</option>
                <option v-for="provider in providers" :key="provider.provider_id" :value="provider.provider_id">
                  {{ provider.provider_name }} · {{ provider.shop_count || 0 }} shops
                </option>
              </select>
              <p class="mt-2 text-sm text-white/45">Use this dropdown to choose the main provider account that will own the new shop.</p>
            </div>
            <div>
              <label class="label">Shop Name *</label>
              <input v-model="shopForm.name" class="field" type="text" placeholder="e.g., Kanoon Footwear" required />
            </div>
            <div>
              <label class="label">Shop Email</label>
              <input v-model="shopForm.email" class="field" type="email" placeholder="optional-shop@email.com" />
            </div>
            <div class="flex flex-wrap gap-3">
              <button class="button-primary" type="submit">Create Shop</button>
              <button class="button-secondary" type="button" @click="closeShopModal">Cancel</button>
            </div>
          </form>
        </div>
      </div>

    </div>
  </div>
</template>

<script>
import {
  ArchiveBoxIcon,
  ChevronRightIcon,
  ClipboardDocumentListIcon,
  CreditCardIcon,
  MegaphoneIcon,
  ShoppingBagIcon,
  UserCircleIcon
} from "@heroicons/vue/24/outline";
import { useAppStore } from "./stores/app";
import { studioApi } from "./services/api";

function profileDefaults() {
  return {
    id: null,
    name: "",
    email: "",
    role: "Buyer",
    phone: "",
    address: ""
  };
}

function shopDefaults(providerId = "") {
  return {
    provider_id: providerId,
    name: "",
    email: ""
  };
}

export default {
  name: "App",
  components: {
    ArchiveBoxIcon,
    ChevronRightIcon,
    ClipboardDocumentListIcon,
    MegaphoneIcon,
    UserCircleIcon
  },
  data() {
    return {
      store: null,
      selectedProfileId: null,
      workspaceTab: "storefront",
      profileForm: profileDefaults(),
      providers: [],
      shopForm: shopDefaults(),
      shopMessage: "",
      showShopModal: false,
      currentSalesBill: null
    };
  },
  computed: {
    ready() {
      return this.store?.ready || false;
    },
    profiles() {
      return this.store?.profiles || [];
    },
    products() {
      return this.store?.products || [];
    },
    selectedProviderInfo() {
      return this.providers.find((provider) => provider.provider_id === this.shopForm.provider_id) || null;
    },
    selectedProviderShops() {
      return this.selectedProviderInfo?.shops || [];
    },
    orders() {
      return this.store?.orders || [];
    },
    featuredProducts() {
      return this.store?.featuredProducts || [];
    },
    inventoryValue() {
      return this.store?.inventoryValue || 0;
    },
    activeProfile() {
      return this.store?.activeProfile || null;
    },
    errorMessage() {
      return this.store?.error || "";
    }
  },
  async mounted() {
    this.store = useAppStore();
    await this.store.initialize();
    this.selectedProfileId = this.store.activeProfileId;
    this.hydrateForms();
    await this.loadProviders();
  },
  methods: {
    money(value) {
      return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 0
      }).format(Number(value || 0));
    },
    formatDate(value) {
      if (!value) return "-";
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return "-";
      return date.toLocaleString("th-TH", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      });
    },
    formatShortDate(value) {
      if (!value) return "-";
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return "-";
      return date.toLocaleDateString("th-TH", {
        year: "numeric",
        month: "short",
        day: "numeric"
      });
    },
    prettyLabel(value) {
      if (!value) return "-";
      return String(value).replaceAll("_", " ").replace(/\w/g, (char) => char.toUpperCase());
    },
    prettyPaymentStatus(value) {
      if (!value) return "-";
      return this.prettyLabel(value);
    },
    paymentBadgeClass(status) {
      const normalized = String(status || "").toLowerCase();
      if (normalized.includes("pending") || normalized.includes("wait") || normalized.includes("await")) {
        return "bg-amber-400/15 text-amber-200";
      }
      if (normalized.includes("fail") || normalized.includes("cancel") || normalized.includes("reject")) {
        return "bg-red-400/15 text-red-200";
      }
      if (normalized.includes("paid") || normalized.includes("success") || normalized.includes("complete")) {
        return "bg-emerald-400/15 text-emerald-200";
      }
      return "bg-white/10 text-white/70";
    },
    openOrderBill(order) {
      this.currentSalesBill = order;
    },
    closeOrderBill() {
      this.currentSalesBill = null;
    },
    hydrateForms() {
      if (this.activeProfile) {
        this.profileForm = { ...this.activeProfile };
      } else {
        this.profileForm = profileDefaults();
      }
      this.selectedProfileId = this.store.activeProfileId;
    },
    async loadProviders() {
      try {
        const data = await studioApi.listProviders();
        this.providers = data.providers || [];
        const fallbackProviderId = this.providers[0]?.provider_id || "";
        if (!this.shopForm.provider_id) {
          this.shopForm.provider_id = fallbackProviderId;
        }
      } catch (error) {
        this.shopMessage = error.message || "Unable to load providers.";
      }
    },
    onProfileChange() {
      this.store.selectProfile(this.selectedProfileId);
      this.profileForm = this.activeProfile ? { ...this.activeProfile } : profileDefaults();
    },
    async submitProfile() {
      await this.store.saveProfile({ ...this.profileForm });
      this.resetProfileForm();
      this.selectedProfileId = this.store.activeProfileId;
    },
    resetProfileForm() {
      this.profileForm = this.activeProfile ? { ...this.activeProfile } : profileDefaults();
    },
    editProfile(profile) {
      this.profileForm = { ...profile };
      this.workspaceTab = "user";
    },
    async removeProfile(id) {
      await this.store.deleteProfile(id);
      this.resetProfileForm();
      this.selectedProfileId = this.store.activeProfileId;
    },
    resetShopForm() {
      this.shopForm = shopDefaults(this.providers[0]?.provider_id || "");
      this.shopMessage = "";
    },
    openShopModal() {
      if (!this.shopForm.provider_id) {
        this.shopForm.provider_id = this.providers[0]?.provider_id || "";
      }
      this.showShopModal = true;
    },
    closeShopModal() {
      this.showShopModal = false;
      this.resetShopForm();
    },
    async submitShop() {
      await studioApi.createProviderShop(this.shopForm.provider_id, {
        name: this.shopForm.name,
        email: this.shopForm.email
      });
      const createdName = this.shopForm.name;
      this.resetShopForm();
      this.shopMessage = `Created shop: ${createdName}`;
      this.showShopModal = false;
      await this.loadProviders();
      await this.store.reloadAll();
    },
    async removeShop(shop) {
      if (!window.confirm(`Delete shop "${shop.provider_name}"?`)) {
        return;
      }
      await studioApi.deleteProviderShop(shop.provider_id);
      this.shopMessage = `Deleted shop: ${shop.provider_name}`;
      await this.loadProviders();
      await this.store.reloadAll();
    }
  },
  watch: {
    activeProfile(nextProfile) {
      if (!this.profileForm.id && nextProfile) {
        this.profileForm = { ...nextProfile };
      }
    }
  }
};
</script>
