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
                :class="workspaceTab === 'overview' ? 'border-red-500 text-red-500' : 'border-transparent text-ink/55 hover:text-ink'"
                @click="workspaceTab = 'overview'"
              >
                ภาพรวม
              </button>
              <button
                class="border-b-2 px-6 py-5 text-lg font-semibold transition"
                :class="workspaceTab === 'ai' ? 'border-red-500 text-red-500' : 'border-transparent text-ink/55 hover:text-ink'"
                @click="workspaceTab = 'ai'"
              >
                AI วิเคราะห์
              </button>
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
            </div>
          </div>

          <div class="p-6">
            <section v-if="workspaceTab === 'overview'" class="space-y-6">
              <article class="rounded-[2rem] border border-white/10 bg-black/20 p-6">
                <div class="panel-header">
                  <div>
                    <p class="text-xs uppercase tracking-[0.22em] text-white/40">Dashboard Overview</p>
                    <h2 class="mt-2 text-2xl font-semibold">ภาพรวมการทำงานของร้าน</h2>
                  </div>
                  <ClipboardDocumentListIcon class="h-6 w-6 text-white/55" />
                </div>

                <div class="mb-6 grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)_minmax(0,1fr)]">
                  <div>
                    <label class="label">Provider Filter</label>
                    <select v-model="overviewFilters.providerId" class="field">
                      <option value="">แสดงทั้งหมด</option>
                      <option v-for="provider in providers" :key="provider.provider_id" :value="provider.provider_id">
                        {{ provider.provider_name }}
                      </option>
                    </select>
                  </div>
                  <div>
                    <label class="label">วัน</label>
                    <input v-model="overviewFilters.day" class="field" type="date" />
                  </div>
                  <div>
                    <label class="label">เดือน / ปี</label>
                    <div class="grid gap-3 sm:grid-cols-2">
                      <select v-model="overviewFilters.month" class="field">
                        <option value="">ทุกเดือน</option>
                        <option v-for="option in monthOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                      </select>
                      <select v-model="overviewFilters.year" class="field">
                        <option value="">ทุกปี</option>
                        <option v-for="year in yearOptions" :key="year" :value="year">{{ year }}</option>
                      </select>
                    </div>
                  </div>
                </div>

                <div class="mb-6 flex flex-wrap gap-3">
                  <button class="button-primary" type="button" @click="applyOverviewFilters">Load Dashboard</button>
                  <button class="button-secondary" type="button" @click="resetOverviewFilters">Reset Filters</button>
                </div>

                <div class="admin-dashboard-grid">
                  <article v-for="card in overviewCards" :key="card.label" class="admin-dashboard-card">
                    <h3>{{ card.label }}</h3>
                    <p class="value">{{ card.value }}</p>
                    <p class="mt-3 text-sm text-white/40">{{ card.note }}</p>
                  </article>
                </div>
              </article>

            </section>

            <section v-else-if="workspaceTab === 'ai'" class="space-y-6">
              <article class="rounded-[2rem] border border-white/10 bg-black/20 p-6">
                <div class="panel-header">
                  <div>
                    <p class="text-xs uppercase tracking-[0.22em] text-white/40">AI Insights</p>
                    <h2 class="mt-2 text-2xl font-semibold">AI วิเคราะห์ร้านแบบอ่านง่าย</h2>
                  </div>
                  <SparklesIcon class="h-6 w-6 text-white/55" />
                </div>

                <div class="mb-6 grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)_minmax(0,1fr)]">
                  <div>
                    <label class="label">เลือก Provider</label>
                    <select v-model="aiFilters.providerId" class="field">
                      <option value="">ทุก provider</option>
                      <option v-for="provider in providers" :key="provider.provider_id" :value="provider.provider_id">
                        {{ provider.provider_name }}
                      </option>
                    </select>
                  </div>
                  <div>
                    <label class="label">เลือกวัน</label>
                    <input v-model="aiFilters.day" class="field" type="date" />
                  </div>
                  <div>
                    <label class="label">เลือกเดือน / ปี</label>
                    <div class="grid gap-3 sm:grid-cols-2">
                      <select v-model="aiFilters.month" class="field">
                        <option value="">ทุกเดือน</option>
                        <option v-for="option in monthOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                      </select>
                      <select v-model="aiFilters.year" class="field">
                        <option value="">ทุกปี</option>
                        <option v-for="year in yearOptions" :key="year" :value="year">{{ year }}</option>
                      </select>
                    </div>
                  </div>
                </div>

                <div class="mb-6 flex flex-wrap gap-3">
                  <button class="button-primary" type="button" @click="applyAiFilters">วิเคราะห์ข้อมูล</button>
                  <button class="button-secondary" type="button" @click="resetAiFilters">ล้างตัวกรอง</button>
                </div>

                <div class="grid gap-4 xl:grid-cols-2">
                  <article v-for="insight in aiInsightCards" :key="insight.title" class="ai-insight-card">
                    <div class="flex items-start justify-between gap-4">
                      <div>
                        <p class="text-xs uppercase tracking-[0.22em] text-white/35">{{ insight.group }}</p>
                        <h3 class="mt-2 text-xl font-semibold text-white">{{ insight.title }}</h3>
                      </div>
                      <span class="chip">{{ insight.status }}</span>
                    </div>
                    <div class="mt-5 grid gap-3 sm:grid-cols-2">
                      <div class="rounded-[1.2rem] border border-white/10 bg-black/25 p-4">
                        <p class="text-xs uppercase tracking-[0.18em] text-white/35">ดูอะไร</p>
                        <p class="mt-2 text-sm leading-6 text-white/70">{{ insight.what }}</p>
                      </div>
                      <div class="rounded-[1.2rem] border border-white/10 bg-black/25 p-4">
                        <p class="text-xs uppercase tracking-[0.18em] text-white/35">เอาไปใช้ทำอะไร</p>
                        <p class="mt-2 text-sm leading-6 text-white/70">{{ insight.action }}</p>
                      </div>
                    </div>
                    <p class="mt-5 text-base leading-7 text-white/85">{{ insight.summary }}</p>
                  </article>
                </div>
              </article>

              <article class="rounded-[2rem] border border-white/10 bg-black/20 p-6">
                <div class="panel-header">
                  <div>
                    <p class="text-xs uppercase tracking-[0.22em] text-white/40">AI Recommendations</p>
                    <h2 class="mt-2 text-2xl font-semibold">สิ่งที่ควรทำต่อ</h2>
                  </div>
                  <LightBulbIcon class="h-6 w-6 text-white/55" />
                </div>

                <div class="grid gap-4 lg:grid-cols-[1fr_1fr]">
                  <div class="space-y-3">
                    <div v-for="(item, index) in aiRecommendedActions" :key="item" class="flex gap-4 rounded-[1.4rem] border border-white/10 bg-white/[0.025] p-4">
                      <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white text-sm font-semibold text-black">{{ index + 1 }}</div>
                      <p class="text-sm leading-6 text-white/75">{{ item }}</p>
                    </div>
                  </div>

                  <div class="rounded-[1.4rem] border border-white/10 bg-white/[0.025] p-4">
                    <label class="label">ถาม AI จากข้อมูลร้าน</label>
                    <textarea v-model="aiQuestion" class="field min-h-[110px]" placeholder="เช่น เดือนนี้ควรโปรโมทสินค้าอะไร หรือ provider ไหนควรติดตาม"></textarea>
                    <div class="mt-4 rounded-[1.2rem] border border-white/10 bg-black/25 p-4">
                      <p class="text-xs uppercase tracking-[0.18em] text-white/35">คำตอบจากข้อมูลตอนนี้</p>
                      <p class="mt-2 text-sm leading-6 text-white/75">{{ aiQuestionAnswer }}</p>
                    </div>
                  </div>
                </div>
              </article>

              <article class="rounded-[2rem] border border-white/10 bg-black/20 p-6">
                <div class="panel-header">
                  <div>
                    <p class="text-xs uppercase tracking-[0.22em] text-white/40">AI Detail Table</p>
                    <h2 class="mt-2 text-2xl font-semibold">อันดับสินค้าที่ AI ใช้วิเคราะห์</h2>
                  </div>
                  <ChartBarIcon class="h-6 w-6 text-white/55" />
                </div>

                <div v-if="aiTopProducts.length" class="overflow-hidden rounded-[1.8rem] border border-white/10 bg-white/[0.025]">
                  <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-white/10 text-sm">
                      <thead class="bg-white/[0.05] text-left text-xs font-semibold uppercase tracking-[0.2em] text-white/45">
                        <tr>
                          <th class="px-5 py-4">สินค้า</th>
                          <th class="px-5 py-4">หมวด</th>
                          <th class="px-5 py-4">จำนวนขาย</th>
                          <th class="px-5 py-4">ยอดขาย</th>
                          <th class="px-5 py-4">สต็อกปัจจุบัน</th>
                          <th class="px-5 py-4">AI แนะนำ</th>
                        </tr>
                      </thead>
                      <tbody class="divide-y divide-white/5 bg-transparent">
                        <tr v-for="product in aiTopProducts" :key="product.id" class="transition hover:bg-white/[0.03]">
                          <td class="px-5 py-4 font-medium text-white">{{ product.name }}</td>
                          <td class="px-5 py-4 text-white/60">{{ product.category || '-' }}</td>
                          <td class="px-5 py-4 text-white/70">{{ product.quantity }}</td>
                          <td class="px-5 py-4 font-medium text-white">{{ money(product.revenue) }}</td>
                          <td class="px-5 py-4 text-white/70">{{ product.stock }}</td>
                          <td class="px-5 py-4 text-white/65">{{ product.advice }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
                <div v-else class="rounded-[1.5rem] border border-dashed border-white/10 px-4 py-8 text-center text-sm text-white/40">
                  ยังไม่มีออเดอร์ในช่วงที่เลือกสำหรับวิเคราะห์
                </div>
              </article>
            </section>

            <section v-else-if="workspaceTab === 'storefront'" class="space-y-6">
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

                <div v-if="selectedProviderInfo" class="mb-5 rounded-[1.5rem] border border-white/10 bg-white/[0.025] p-4">
                  <div class="flex items-center gap-4">
                    <img
                      v-if="selectedProviderInfo.logo_url"
                      :src="selectedProviderInfo.logo_url"
                      :alt="selectedProviderInfo.provider_name"
                      class="h-14 w-14 rounded-2xl object-cover"
                    />
                    <div
                      v-else
                      class="flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-black/20 text-lg font-semibold text-white/75"
                    >
                      {{ providerInitial(selectedProviderInfo.provider_name) }}
                    </div>
                    <div>
                      <p class="font-medium text-white">{{ selectedProviderInfo.provider_name }}</p>
                      <p class="mt-1 text-sm text-white/45">{{ selectedProviderInfo.shop_count || 0 }} shops</p>
                    </div>
                  </div>
                  <div v-if="selectedProviderInfo.shop_names?.length" class="mt-4 flex flex-wrap gap-2">
                    <span
                      v-for="shopName in selectedProviderInfo.shop_names"
                      :key="shopName"
                      class="rounded-full border border-white/10 px-3 py-1 text-xs text-white/60"
                    >
                      {{ shopName }}
                    </span>
                  </div>
                </div>

                <div v-if="selectedProviderShops.length" class="space-y-3">
                  <div
                    v-for="shop in selectedProviderShops"
                    :key="shop.provider_id"
                    class="rounded-[1.5rem] border border-white/10 bg-white/[0.025] px-4 py-4"
                  >
                    <div class="flex items-start justify-between gap-3">
                      <div class="flex items-center gap-4">
                        <img
                          v-if="shop.logo_url"
                          :src="shop.logo_url"
                          :alt="shop.provider_name"
                          class="h-14 w-14 rounded-2xl object-cover"
                        />
                        <div
                          v-else
                          class="flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-black/20 text-lg font-semibold text-white/75"
                        >
                          {{ providerInitial(shop.provider_name) }}
                        </div>
                        <div>
                          <p class="font-medium">{{ shop.provider_name }}</p>
                          <p class="mt-1 text-sm text-white/45">{{ shop.provider_id }}</p>
                          <p class="mt-2 text-xs uppercase tracking-[0.16em] text-white/35">{{ shop.product_count || 0 }} products in this shop</p>
                        </div>
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

              <div class="mb-5 grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)_minmax(0,1fr)]">
                <div>
                  <label class="label">Provider Filter</label>
                  <select v-model="orderFilters.providerId" class="field">
                    <option value="">แสดงทั้งหมด</option>
                    <option v-for="provider in providers" :key="provider.provider_id" :value="provider.provider_id">
                      {{ provider.provider_name }}
                    </option>
                  </select>
                </div>
                <div>
                  <label class="label">เดือน</label>
                  <select v-model="orderFilters.month" class="field">
                    <option value="">ทุกเดือน</option>
                    <option v-for="option in monthOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                  </select>
                </div>
                <div>
                  <label class="label">ปี</label>
                  <select v-model="orderFilters.year" class="field">
                    <option value="">ทุกปี</option>
                    <option v-for="year in yearOptions" :key="year" :value="year">{{ year }}</option>
                  </select>
                </div>
              </div>
              <div class="mb-5 grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto_auto]">
                <div>
                  <label class="label">วัน</label>
                  <input v-model="orderFilters.day" class="field" type="date" />
                </div>
                <div class="flex items-end">
                  <button class="button-secondary w-full" type="button" @click="resetOrderFilters">Reset Filters</button>
                </div>
                <div class="flex items-end">
                  <button class="button-primary w-full" type="button" @click="applyOrderFilters">Load Orders</button>
                </div>
                <div class="flex items-end">
                  <button class="button-secondary w-full" type="button" @click="exportOrdersToExcel">Export Excel</button>
                </div>
              </div>

              <div v-if="filteredOrders.length" class="overflow-hidden rounded-[1.8rem] border border-white/10 bg-white/[0.025]">
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
                        v-for="(order, index) in filteredOrders"
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
                No sales history for this filter.
              </div>
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
  ChartBarIcon,
  ChevronRightIcon,
  ClipboardDocumentListIcon,
  LightBulbIcon,
  MegaphoneIcon,
  SparklesIcon,
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
    ChartBarIcon,
    ChevronRightIcon,
    ClipboardDocumentListIcon,
    LightBulbIcon,
    MegaphoneIcon,
    SparklesIcon,
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
      currentSalesBill: null,
      orderFilters: {
        providerId: "",
        day: "",
        month: "",
        year: ""
      },
      overviewFilters: {
        providerId: "",
        day: "",
        month: "",
        year: ""
      },
      aiFilters: {
        providerId: "",
        day: "",
        month: "",
        year: ""
      },
      aiQuestion: "เดือนนี้ควรโฟกัสเรื่องอะไรเป็นอันดับแรก"
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
    },
    monthOptions() {
      return [
        { value: "1", label: "มกราคม" },
        { value: "2", label: "กุมภาพันธ์" },
        { value: "3", label: "มีนาคม" },
        { value: "4", label: "เมษายน" },
        { value: "5", label: "พฤษภาคม" },
        { value: "6", label: "มิถุนายน" },
        { value: "7", label: "กรกฎาคม" },
        { value: "8", label: "สิงหาคม" },
        { value: "9", label: "กันยายน" },
        { value: "10", label: "ตุลาคม" },
        { value: "11", label: "พฤศจิกายน" },
        { value: "12", label: "ธันวาคม" }
      ];
    },
    yearOptions() {
      const currentYear = new Date().getFullYear();
      return Array.from({ length: 6 }, (_, index) => String(currentYear - index));
    },
    filteredOrders() {
      return this.filterOrders(this.orders, this.orderFilters);
    },
    overviewFilteredOrders() {
      return this.filterOrders(this.orders, this.overviewFilters);
    },
    overviewStats() {
      const orders = this.overviewFilteredOrders;
      const totalRevenue = orders.reduce((sum, order) => sum + Number(order.total || 0), 0);
      const providerCount = new Set(orders.flatMap((order) => this.getOrderProviderIds(order))).size;
      const paidOrders = orders.filter((order) => this.isPaidStatus(order.payment_status)).length;
      const uniqueCustomers = new Set(
        orders.map((order) => String(order.user_name || order.customer_email || order.profile_id || "").trim()).filter(Boolean)
      ).size;
      return {
        totalOrders: orders.length,
        totalRevenue,
        avgOrderValue: orders.length ? totalRevenue / orders.length : 0,
        providerCount,
        paidOrders,
        uniqueCustomers,
        paidRate: orders.length ? (paidOrders / orders.length) * 100 : 0
      };
    },
    overviewCards() {
      const stats = this.overviewStats;
      return [
        {
          label: "Orders",
          value: String(stats.totalOrders),
          note: stats.uniqueCustomers + " unique customers in view"
        },
        {
          label: "Revenue",
          value: this.money(stats.totalRevenue),
          note: "Combined value from filtered orders"
        },
        {
          label: "Avg Order Value",
          value: this.money(stats.avgOrderValue),
          note: "Average basket size"
        },
        {
          label: "Providers",
          value: String(stats.providerCount),
          note: "Unique providers contributing to this view"
        },
        {
          label: "Paid Orders",
          value: String(stats.paidOrders),
          note: Math.round(stats.paidRate) + "% paid rate"
        }
      ];
    },
    aiFilteredOrders() {
      return this.filterOrders(this.orders, this.aiFilters);
    },
    aiMetrics() {
      const orders = this.aiFilteredOrders;
      const totalRevenue = orders.reduce((sum, order) => sum + Number(order.total || 0), 0);
      const pendingOrders = orders.filter((order) => String(order.payment_status || "").toLowerCase().includes("pending")).length;
      const paidOrders = orders.filter((order) => this.isPaidStatus(order.payment_status)).length;
      const lowStockProducts = this.products.filter((product) => Number(product.stock || 0) <= 5).length;
      return {
        orders: orders.length,
        totalRevenue,
        avgOrderValue: orders.length ? totalRevenue / orders.length : 0,
        pendingOrders,
        paidOrders,
        paidRate: orders.length ? (paidOrders / orders.length) * 100 : 0,
        lowStockProducts
      };
    },
    aiProductRows() {
      const productMap = new Map();
      this.products.forEach((product) => {
        productMap.set(String(product.id), {
          id: String(product.id),
          name: product.name || "Unknown product",
          category: product.category || "-",
          stock: Number(product.stock || 0),
          quantity: 0,
          revenue: 0
        });
      });

      this.aiFilteredOrders.forEach((order) => {
        (order.items || []).forEach((item) => {
          const id = String(item.productId || item.product_id || item.name || "unknown");
          const row = productMap.get(id) || {
            id,
            name: item.name || "Unknown product",
            category: item.category || "-",
            stock: "-",
            quantity: 0,
            revenue: 0
          };
          row.quantity += Number(item.quantity || 0);
          row.revenue += Number(item.lineTotal || Number(item.quantity || 0) * Number(item.price || 0));
          productMap.set(id, row);
        });
      });

      return Array.from(productMap.values()).filter((row) => row.quantity > 0 || Number(row.stock) <= 5);
    },
    aiTopProducts() {
      return this.aiProductRows
        .map((row) => ({
          ...row,
          advice: Number(row.stock) <= 5
            ? "ควรเติมสต็อกก่อนเสียโอกาสขาย"
            : row.quantity > 0
              ? "มีแรงขาย ใช้ทำโปรโมชันต่อได้"
              : "ยังไม่เร่งด่วน"
        }))
        .sort((a, b) => Number(b.revenue || 0) - Number(a.revenue || 0))
        .slice(0, 8);
    },
    aiTopProvider() {
      const providerRevenue = new Map();
      this.aiFilteredOrders.forEach((order) => {
        const providerIds = this.getOrderProviderIds(order);
        const splitRevenue = providerIds.length ? Number(order.total || 0) / providerIds.length : Number(order.total || 0);
        providerIds.forEach((providerId) => {
          providerRevenue.set(providerId, Number(providerRevenue.get(providerId) || 0) + splitRevenue);
        });
      });
      const topEntry = Array.from(providerRevenue.entries()).sort((a, b) => b[1] - a[1])[0];
      if (!topEntry) return { name: "-", revenue: 0 };
      const provider = this.providers.find((entry) => entry.provider_id === topEntry[0]);
      return { name: provider?.provider_name || topEntry[0], revenue: topEntry[1] };
    },
    aiBestProduct() {
      return this.aiTopProducts.find((product) => product.quantity > 0) || null;
    },
    aiInsightCards() {
      const metrics = this.aiMetrics;
      const bestProduct = this.aiBestProduct;
      const lowStockProduct = this.aiTopProducts.find((product) => Number(product.stock) <= 5);
      const topProvider = this.aiTopProvider;
      return [
        {
          group: "Sales",
          title: "ยอดขายช่วงที่เลือก",
          status: metrics.orders ? "มีข้อมูล" : "รอข้อมูล",
          what: "ดูจำนวนออเดอร์ ยอดขายรวม และค่าเฉลี่ยต่อบิลจากตัวกรองด้านบน",
          action: metrics.orders ? "ใช้เช็กว่าช่วงนี้ร้านเดินดีไหม และควรเร่งยอดเพิ่มหรือรักษาระดับเดิม" : "ยังไม่มีออเดอร์ในช่วงนี้ ลองเปลี่ยนวัน เดือน ปี หรือ provider",
          summary: metrics.orders
            ? `มี ${metrics.orders} ออเดอร์ ยอดรวม ${this.money(metrics.totalRevenue)} ค่าเฉลี่ยต่อบิล ${this.money(metrics.avgOrderValue)}`
            : "ยังไม่พบยอดขายในช่วงที่เลือก"
        },
        {
          group: "Stock",
          title: "สินค้าที่ควรเติม",
          status: lowStockProduct ? "ควรดู" : "ปกติ",
          what: "ดูสินค้าที่สต็อกต่ำและสินค้าที่มีแรงขายในช่วงที่เลือก",
          action: lowStockProduct ? "เติมสินค้าที่ขายได้และสต็อกต่ำก่อน เพื่อไม่ให้เสียยอดขาย" : "ยังไม่เห็นสินค้าเสี่ยงหมดชัดเจน ตรวจซ้ำหลังมีออเดอร์เพิ่ม",
          summary: lowStockProduct
            ? `${lowStockProduct.name} เหลือ ${lowStockProduct.stock} ชิ้น และมีข้อมูลขาย ${lowStockProduct.quantity} ชิ้น`
            : `มีสินค้าใกล้หมด ${metrics.lowStockProducts} รายการจากคลังทั้งหมด`
        },
        {
          group: "Order Follow-up",
          title: "ออเดอร์ที่ควรติดตาม",
          status: metrics.pendingOrders ? "ต้องตาม" : "เรียบร้อย",
          what: "ดูบิลที่ยัง pending หรือยังไม่จบ flow การชำระเงิน",
          action: metrics.pendingOrders ? "ติดตามการชำระหรือสลิปก่อน เพื่อให้ยอดไม่ค้างในระบบ" : "ยังไม่มีบิล pending ในช่วงนี้",
          summary: metrics.pendingOrders
            ? `มี ${metrics.pendingOrders} ออเดอร์ที่ยัง pending คิดเป็น ${Math.round(100 - metrics.paidRate)}% ของช่วงนี้`
            : `อัตราชำระสำเร็จ ${Math.round(metrics.paidRate)}% ในช่วงที่เลือก`
        },
        {
          group: "Provider",
          title: "Provider ที่ทำผลงานเด่น",
          status: topProvider.revenue ? "พบอันดับ" : "รอข้อมูล",
          what: "ดู provider ที่สร้างยอดขายสูงสุดในช่วงที่เลือก",
          action: topProvider.revenue ? "ใช้คุยเรื่องสต็อก โปรโมชัน หรือขยายสินค้าที่ขายดี" : "ยังไม่มี provider เด่นจากตัวกรองนี้",
          summary: topProvider.revenue
            ? `${topProvider.name} ทำยอดประมาณ ${this.money(topProvider.revenue)} ในช่วงนี้`
            : "ยังไม่พบยอดขายแยก provider"
        }
      ];
    },
    aiRecommendedActions() {
      const actions = [];
      const metrics = this.aiMetrics;
      const bestProduct = this.aiBestProduct;
      const lowStockProduct = this.aiTopProducts.find((product) => Number(product.stock) <= 5);
      if (lowStockProduct) {
        actions.push(`เติมสต็อก ${lowStockProduct.name} ก่อน เพราะเหลือ ${lowStockProduct.stock} ชิ้น`);
      }
      if (bestProduct) {
        actions.push(`ลองทำโปรโมชันกับ ${bestProduct.name} เพราะเป็นสินค้าที่มียอดขายเด่นในช่วงนี้`);
      }
      if (metrics.pendingOrders) {
        actions.push(`ติดตาม ${metrics.pendingOrders} ออเดอร์ pending เพื่อปิดยอดขายให้เร็วขึ้น`);
      }
      if (this.aiTopProvider.revenue) {
        actions.push(`คุยกับ ${this.aiTopProvider.name} เรื่องสินค้าขายดีและแผนเติมของ`);
      }
      if (!actions.length) {
        actions.push("ข้อมูลช่วงนี้ยังน้อย แนะนำให้ดูภาพรวมทุก provider ก่อน แล้วค่อยกรองลึกลงมา");
      }
      return actions.slice(0, 4);
    },
    aiQuestionAnswer() {
      const question = String(this.aiQuestion || "").toLowerCase();
      const bestProduct = this.aiBestProduct;
      const lowStockProduct = this.aiTopProducts.find((product) => Number(product.stock) <= 5);
      if (question.includes("สินค้า") || question.includes("โปรโมท") || question.includes("โปรโมชัน")) {
        return bestProduct
          ? `ควรเริ่มจาก ${bestProduct.name} เพราะมีจำนวนขาย ${bestProduct.quantity} ชิ้น และทำยอด ${this.money(bestProduct.revenue)} ในช่วงที่เลือก`
          : "ยังไม่มีสินค้าขายเด่นในตัวกรองนี้ ลองเปลี่ยนช่วงเวลาเป็นทั้งเดือนหรือดูทุก provider";
      }
      if (question.includes("สต็อก") || question.includes("เติม")) {
        return lowStockProduct
          ? `ควรเติม ${lowStockProduct.name} ก่อน เพราะสต็อกเหลือ ${lowStockProduct.stock} ชิ้น`
          : "ยังไม่มีสินค้าเสี่ยงหมดชัดเจนในข้อมูลชุดนี้";
      }
      if (question.includes("provider") || question.includes("ร้าน")) {
        return this.aiTopProvider.revenue
          ? `${this.aiTopProvider.name} เป็น provider ที่เด่นสุดในช่วงนี้ ทำยอดประมาณ ${this.money(this.aiTopProvider.revenue)}`
          : "ยังไม่มี provider ที่เด่นพอจากตัวกรองนี้";
      }
      return this.aiRecommendedActions[0] || "เริ่มจากดูยอดขายรวม สต็อกต่ำ และออเดอร์ pending ก่อน จะเห็นงานที่ควรทำเร็วที่สุด";
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
      return String(value).replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
    },
    providerInitial(value) {
      return String(value || "S").trim().charAt(0).toUpperCase() || "S";
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
    isPaidStatus(status) {
      const normalized = String(status || "").toLowerCase();
      return normalized.includes("paid") || normalized.includes("success") || normalized.includes("complete");
    },
    getOrderProviderIds(order) {
      return [...new Set((order?.items || []).map((item) => String(item.providerId || item.provider_id || "").trim()).filter(Boolean))];
    },
    getOrderProviderNames(order) {
      const ids = this.getOrderProviderIds(order);
      if (!ids.length) {
        return ["-"];
      }
      return ids.map((providerId) => {
        const provider = this.providers.find((entry) => entry.provider_id === providerId);
        return provider?.provider_name || providerId;
      });
    },
    filterOrders(orders, filters = {}) {
      const providerId = String(filters.providerId || "").trim();
      const day = String(filters.day || "").trim();
      const month = String(filters.month || "").trim();
      const year = String(filters.year || "").trim();
      const dayParts = day ? this.parseDateParts(day) : null;

      return (orders || []).filter((order) => {
        const providerIds = this.getOrderProviderIds(order);
        if (providerId && !providerIds.includes(providerId)) {
          return false;
        }

        const parts = this.parseDateParts(order.created_at);
        if (!parts) {
          return false;
        }

        if (dayParts) {
          return parts.year === dayParts.year && parts.month === dayParts.month && parts.day === dayParts.day;
        }

        if (month && String(parts.month) !== String(Number(month))) {
          return false;
        }
        if (year && String(parts.year) !== String(Number(year))) {
          return false;
        }
        return true;
      });
    },
    parseDateParts(value) {
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) {
        return null;
      }
      return {
        year: date.getFullYear(),
        month: date.getMonth() + 1,
        day: date.getDate()
      };
    },
    resetOrderFilters() {
      this.orderFilters = {
        providerId: "",
        day: "",
        month: "",
        year: ""
      };
    },
    resetOverviewFilters() {
      this.overviewFilters = {
        providerId: "",
        day: "",
        month: "",
        year: ""
      };
    },
    resetAiFilters() {
      this.aiFilters = {
        providerId: "",
        day: "",
        month: "",
        year: ""
      };
    },
    applyAiFilters() {
      return this.aiFilteredOrders.length;
    },
    applyOrderFilters() {
      return this.filteredOrders.length;
    },
    applyOverviewFilters() {
      return this.overviewFilteredOrders.length;
    },
    exportOrdersToExcel(scope = "orders") {
      const sourceOrders = scope === "overview" ? this.overviewFilteredOrders : this.filteredOrders;
      const rows = sourceOrders.map((order, index) => ({
        "#": index + 1,
        Date: this.formatDate(order.created_at),
        Invoice: order.invoice_number || "-",
        Provider: this.getOrderProviderNames(order).join(" · ") || "-",
        Customer: order.user_name || "-",
        Email: order.customer_email || "-",
        Payment: this.prettyPaymentStatus(order.payment_status),
        Method: this.prettyLabel(order.payment_method),
        Total: Number(order.total || 0),
        Items: (order.items || []).length
      }));

      if (!window.XLSX) {
        window.alert("Excel library is loading, please try again in a moment.");
        return;
      }

      const worksheet = window.XLSX.utils.json_to_sheet(rows);
      const workbook = window.XLSX.utils.book_new();
      const sheetName = scope === "overview" ? "Overview" : "Orders";
      window.XLSX.utils.book_append_sheet(workbook, worksheet, sheetName);
      const dateStamp = new Date().toISOString().slice(0, 10);
      window.XLSX.writeFile(workbook, sheetName.toLowerCase() + "-" + dateStamp + ".xlsx");
    },
    exportOverviewToExcel() {
      this.exportOrdersToExcel("overview");
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
